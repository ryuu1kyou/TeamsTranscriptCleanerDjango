"""
Views for transcript management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import os

from .models import TranscriptDocument
from ..wordlists.models import WordList
from ..corrections.models import CorrectionJob
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from processing.csv_parser import parse_csv_text
from processing.openai_service import correct_text, estimate_cost


@login_required
def transcript_list(request):
    """List all transcripts for the current user."""
    transcripts = TranscriptDocument.objects.filter(user=request.user)
    return render(request, 'transcripts/list.html', {'transcripts': transcripts})


@login_required
def main_workspace(request):
    """Main workspace with Streamlit-like interface."""
    return render(request, 'transcripts/main_workspace.html')


@login_required
def transcript_detail(request, pk):
    """Display transcript details."""
    transcript = get_object_or_404(TranscriptDocument, pk=pk, user=request.user)
    correction_jobs = transcript.correction_jobs.all()
    return render(request, 'transcripts/detail.html', {
        'transcript': transcript,
        'correction_jobs': correction_jobs
    })


@login_required
def transcript_upload(request):
    """Upload a new transcript."""
    if request.method == 'POST':
        title = request.POST.get('title', '')
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            messages.error(request, 'ファイルを選択してください。')
            return render(request, 'transcripts/upload.html')
        
        if not uploaded_file.name.lower().endswith('.txt'):
            messages.error(request, 'テキストファイル(.txt)のみアップロード可能です。')
            return render(request, 'transcripts/upload.html')
        
        if uploaded_file.size > settings.PROCESSING_MAX_FILE_SIZE:
            messages.error(request, 'ファイルサイズが大きすぎます。')
            return render(request, 'transcripts/upload.html')
        
        try:
            # Read file content
            content = uploaded_file.read().decode('utf-8')
            
            # Create transcript document
            transcript = TranscriptDocument.objects.create(
                user=request.user,
                title=title or uploaded_file.name,
                original_filename=uploaded_file.name,
                content=content,
                file_size=uploaded_file.size
            )
            
            # Save the file
            transcript.file.save(uploaded_file.name, uploaded_file)
            
            messages.success(request, 'トランスクリプトがアップロードされました。')
            return redirect('transcripts:detail', pk=transcript.pk)
            
        except UnicodeDecodeError:
            messages.error(request, 'ファイルの文字エンコーディングが正しくありません。UTF-8でエンコードされたファイルを使用してください。')
        except Exception as e:
            messages.error(request, f'アップロード中にエラーが発生しました: {str(e)}')
    
    return render(request, 'transcripts/upload.html')


@login_required
def transcript_process(request):
    """Main processing page."""
    if request.method == 'GET':
        transcripts = TranscriptDocument.objects.filter(user=request.user)
        wordlists = WordList.objects.filter(user=request.user, is_active=True)
        
        return render(request, 'transcripts/process.html', {
            'transcripts': transcripts,
            'wordlists': wordlists,
            'model_choices': CorrectionJob.MODEL_CHOICES,
            'mode_choices': CorrectionJob.PROCESSING_MODE_CHOICES,
        })
    
    elif request.method == 'POST':
        transcript_id = request.POST.get('transcript_id')
        processing_mode = request.POST.get('processing_mode', 'proofreading')
        model_used = request.POST.get('model_used', 'gpt-4o')
        custom_prompt = request.POST.get('custom_prompt', '')
        wordlist_id = request.POST.get('wordlist_id')
        
        try:
            transcript = get_object_or_404(TranscriptDocument, pk=transcript_id, user=request.user)
            
            # Get wordlist if specified
            wordlist = None
            if wordlist_id:
                wordlist = get_object_or_404(WordList, pk=wordlist_id, user=request.user)
            
            # Check user's API budget
            estimated_cost = estimate_cost(transcript.content, model_used)
            if not request.user.can_use_api(estimated_cost):
                messages.error(request, 'API使用制限に達しています。制限を増やすか、管理者にお問い合わせください。')
                return redirect('transcripts:process')
            
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
                
                messages.success(request, f'処理が完了しました。コスト: ${cost:.4f}')
                return redirect('corrections:job_detail', pk=job.pk)
                
            except Exception as e:
                job.mark_as_failed(str(e))
                messages.error(request, f'処理中にエラーが発生しました: {str(e)}')
                
        except Exception as e:
            messages.error(request, f'エラーが発生しました: {str(e)}')
    
    return redirect('transcripts:process')


@login_required
def transcript_delete(request, pk):
    """Delete a transcript."""
    transcript = get_object_or_404(TranscriptDocument, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete the file
        if transcript.file:
            default_storage.delete(transcript.file.name)
        
        transcript.delete()
        messages.success(request, 'トランスクリプトが削除されました。')
        return redirect('transcripts:list')
    
    return render(request, 'transcripts/delete.html', {'transcript': transcript})


@method_decorator(csrf_exempt, name='dispatch')
class TranscriptAPIView(View):
    """API view for transcript operations."""
    
    def post(self, request):
        """Handle transcript upload via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            content = data.get('content', '')
            
            if not content:
                return JsonResponse({'error': 'Content is required'}, status=400)
            
            transcript = TranscriptDocument.objects.create(
                user=request.user,
                title=title or 'API Upload',
                original_filename='api_upload.txt',
                content=content,
                file_size=len(content.encode('utf-8'))
            )
            
            return JsonResponse({
                'id': transcript.pk,
                'title': transcript.title,
                'character_count': transcript.character_count,
                'word_count': transcript.word_count,
                'created_at': transcript.created_at.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get transcript list via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        transcripts = TranscriptDocument.objects.filter(user=request.user)
        data = []
        
        for transcript in transcripts:
            data.append({
                'id': transcript.pk,
                'title': transcript.title,
                'character_count': transcript.character_count,
                'word_count': transcript.word_count,
                'is_processed': transcript.is_processed,
                'created_at': transcript.created_at.isoformat()
            })
        
        return JsonResponse({'transcripts': data})