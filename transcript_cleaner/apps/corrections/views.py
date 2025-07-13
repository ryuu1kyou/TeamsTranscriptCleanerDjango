"""
Views for correction job management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import CorrectionJob
from ..transcripts.models import TranscriptDocument
from ..wordlists.models import WordList
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from processing.csv_parser import parse_csv_text
from processing.openai_service import correct_text, estimate_cost


@login_required
def job_list(request):
    """List all correction jobs for the current user."""
    jobs = CorrectionJob.objects.filter(user=request.user)
    return render(request, 'corrections/job_list.html', {'jobs': jobs})


@login_required
def job_detail(request, pk):
    """Display correction job details."""
    job = get_object_or_404(CorrectionJob, pk=pk, user=request.user)
    return render(request, 'corrections/job_detail.html', {'job': job})


@login_required
def job_retry(request, pk):
    """Retry a failed correction job."""
    job = get_object_or_404(CorrectionJob, pk=pk, user=request.user)
    
    if job.status not in ['failed', 'cancelled']:
        messages.error(request, 'このジョブは再試行できません。')
        return redirect('corrections:job_detail', pk=job.pk)
    
    if request.method == 'POST':
        # Check user's API budget
        estimated_cost = estimate_cost(job.transcript.content, job.model_used)
        if not request.user.can_use_api(estimated_cost):
            messages.error(request, 'API使用制限に達しています。')
            return redirect('corrections:job_detail', pk=job.pk)
        
        # Get correction words from wordlist
        correction_words = []
        if job.wordlist:
            correction_words = job.wordlist.get_word_pairs()
        
        try:
            job.status = 'pending'
            job.retry_count += 1
            job.error_message = ''
            job.save()
            
            job.mark_as_processing()
            
            corrected_text, cost, input_tokens, output_tokens = correct_text(
                processing_mode=job.processing_mode,
                user_custom_prompt=job.custom_prompt,
                input_text=job.transcript.content,
                correction_words=correction_words,
                model=job.model_used
            )
            
            job.mark_as_completed(corrected_text, cost, input_tokens, output_tokens)
            
            messages.success(request, f'再処理が完了しました。コスト: ${cost:.4f}')
            
        except Exception as e:
            job.mark_as_failed(str(e))
            messages.error(request, f'再処理中にエラーが発生しました: {str(e)}')
    
    return redirect('corrections:job_detail', pk=job.pk)


@login_required
def job_cancel(request, pk):
    """Cancel a pending or processing job."""
    job = get_object_or_404(CorrectionJob, pk=pk, user=request.user)
    
    if job.status not in ['pending', 'processing']:
        messages.error(request, 'このジョブはキャンセルできません。')
        return redirect('corrections:job_detail', pk=job.pk)
    
    if request.method == 'POST':
        job.status = 'cancelled'
        job.save()
        messages.success(request, 'ジョブがキャンセルされました。')
    
    return redirect('corrections:job_detail', pk=job.pk)


@login_required
def job_download(request, pk):
    """Download corrected text as a file."""
    job = get_object_or_404(CorrectionJob, pk=pk, user=request.user)
    
    if not job.is_successful or not job.corrected_content:
        messages.error(request, 'ダウンロード可能な結果がありません。')
        return redirect('corrections:job_detail', pk=job.pk)
    
    response = HttpResponse(job.corrected_content, content_type='text/plain; charset=utf-8')
    filename = f"corrected_{job.transcript.title}_{job.pk}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def job_copy_to_new(request, pk):
    """Copy corrected text to create a new transcript."""
    job = get_object_or_404(CorrectionJob, pk=pk, user=request.user)
    
    if not job.is_successful or not job.corrected_content:
        messages.error(request, 'コピー可能な結果がありません。')
        return redirect('corrections:job_detail', pk=job.pk)
    
    if request.method == 'POST':
        new_title = request.POST.get('title', f"{job.transcript.title} (corrected)")
        
        new_transcript = TranscriptDocument.objects.create(
            user=request.user,
            title=new_title,
            original_filename=f"corrected_{job.transcript.original_filename}",
            content=job.corrected_content,
            file_size=len(job.corrected_content.encode('utf-8'))
        )
        
        messages.success(request, '訂正結果が新しいトランスクリプトとして保存されました。')
        return redirect('transcripts:detail', pk=new_transcript.pk)
    
    return render(request, 'corrections/copy_to_new.html', {'job': job})


@method_decorator(csrf_exempt, name='dispatch')
class CorrectionAPIView(View):
    """API view for correction operations."""
    
    def post(self, request):
        """Create a new correction job via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            transcript_id = data.get('transcript_id')
            processing_mode = data.get('processing_mode', 'proofreading')
            model_used = data.get('model_used', 'gpt-4o')
            custom_prompt = data.get('custom_prompt', '')
            wordlist_id = data.get('wordlist_id')
            
            if not transcript_id:
                return JsonResponse({'error': 'transcript_id is required'}, status=400)
            
            transcript = get_object_or_404(TranscriptDocument, pk=transcript_id, user=request.user)
            
            # Get wordlist if specified
            wordlist = None
            if wordlist_id:
                wordlist = get_object_or_404(WordList, pk=wordlist_id, user=request.user)
            
            # Check user's API budget
            estimated_cost = estimate_cost(transcript.content, model_used)
            if not request.user.can_use_api(estimated_cost):
                return JsonResponse({'error': 'API usage limit exceeded'}, status=403)
            
            # Create correction job
            job = CorrectionJob.objects.create(
                user=request.user,
                transcript=transcript,
                wordlist=wordlist,
                processing_mode=processing_mode,
                custom_prompt=custom_prompt,
                model_used=model_used
            )
            
            # Process the transcript
            correction_words = []
            if wordlist:
                correction_words = wordlist.get_word_pairs()
            
            try:
                job.mark_as_processing()
                
                corrected_text, cost, input_tokens, output_tokens = correct_text(
                    processing_mode=processing_mode,
                    user_custom_prompt=custom_prompt,
                    input_text=transcript.content,
                    correction_words=correction_words,
                    model=model_used
                )
                
                job.mark_as_completed(corrected_text, cost, input_tokens, output_tokens)
                
                return JsonResponse({
                    'job_id': job.pk,
                    'status': job.status,
                    'corrected_content': job.corrected_content,
                    'cost': float(job.cost),
                    'input_tokens': job.input_tokens,
                    'output_tokens': job.output_tokens
                })
                
            except Exception as e:
                job.mark_as_failed(str(e))
                return JsonResponse({'error': str(e)}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get correction job list via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        jobs = CorrectionJob.objects.filter(user=request.user)
        data = []
        
        for job in jobs:
            data.append({
                'id': job.pk,
                'transcript_title': job.transcript.title,
                'processing_mode': job.processing_mode,
                'status': job.status,
                'model_used': job.model_used,
                'cost': float(job.cost),
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            })
        
        return JsonResponse({'jobs': data})