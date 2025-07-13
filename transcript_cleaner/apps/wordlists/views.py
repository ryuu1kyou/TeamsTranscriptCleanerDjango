"""
Views for word list management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import WordList, SharedWordList
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from processing.csv_parser import parse_csv_text, validate_csv_format


@login_required
def wordlist_list(request):
    """List all word lists for the current user."""
    wordlists = WordList.objects.filter(user=request.user)
    shared_wordlists = WordList.objects.filter(
        shared_access__user=request.user,
        is_shared=True
    ).distinct()
    
    return render(request, 'wordlists/list.html', {
        'wordlists': wordlists,
        'shared_wordlists': shared_wordlists
    })


@login_required
def wordlist_detail(request, pk):
    """Display word list details."""
    wordlist = get_object_or_404(WordList, pk=pk)
    
    # Check access permissions
    if wordlist.user != request.user:
        if not wordlist.is_shared or not SharedWordList.objects.filter(
            wordlist=wordlist, user=request.user
        ).exists():
            messages.error(request, 'このワードリストにアクセスする権限がありません。')
            return redirect('wordlists:list')
    
    word_pairs = wordlist.get_word_pairs()
    return render(request, 'wordlists/detail.html', {
        'wordlist': wordlist,
        'word_pairs': word_pairs
    })


@login_required
def wordlist_create(request):
    """Create a new word list."""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        csv_content = request.POST.get('csv_content', '')
        csv_file = request.FILES.get('csv_file')
        
        if not name:
            messages.error(request, 'ワードリスト名を入力してください。')
            return render(request, 'wordlists/create.html')
        
        # Check if name already exists for this user
        if WordList.objects.filter(user=request.user, name=name).exists():
            messages.error(request, 'この名前のワードリストは既に存在します。')
            return render(request, 'wordlists/create.html')
        
        # Handle CSV file upload
        if csv_file:
            try:
                csv_content = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                messages.error(request, 'CSVファイルの文字エンコーディングが正しくありません。')
                return render(request, 'wordlists/create.html')
        
        if not csv_content.strip():
            messages.error(request, 'CSVコンテンツまたはファイルを入力してください。')
            return render(request, 'wordlists/create.html')
        
        # Validate CSV format
        errors = validate_csv_format(csv_content)
        if errors:
            for error in errors:
                messages.error(request, f'CSV形式エラー: {error}')
            return render(request, 'wordlists/create.html')
        
        try:
            wordlist = WordList.objects.create(
                user=request.user,
                name=name,
                description=description,
                csv_content=csv_content
            )
            
            if csv_file:
                wordlist.csv_file.save(csv_file.name, csv_file)
            
            messages.success(request, 'ワードリストが作成されました。')
            return redirect('wordlists:detail', pk=wordlist.pk)
            
        except Exception as e:
            messages.error(request, f'作成中にエラーが発生しました: {str(e)}')
    
    return render(request, 'wordlists/create.html')


@login_required
def wordlist_edit(request, pk):
    """Edit an existing word list."""
    wordlist = get_object_or_404(WordList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        csv_content = request.POST.get('csv_content', '')
        csv_file = request.FILES.get('csv_file')
        is_shared = request.POST.get('is_shared') == 'on'
        
        if not name:
            messages.error(request, 'ワードリスト名を入力してください。')
            return render(request, 'wordlists/edit.html', {'wordlist': wordlist})
        
        # Check if name already exists for this user (excluding current wordlist)
        if WordList.objects.filter(user=request.user, name=name).exclude(pk=pk).exists():
            messages.error(request, 'この名前のワードリストは既に存在します。')
            return render(request, 'wordlists/edit.html', {'wordlist': wordlist})
        
        # Handle CSV file upload
        if csv_file:
            try:
                csv_content = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                messages.error(request, 'CSVファイルの文字エンコーディングが正しくありません。')
                return render(request, 'wordlists/edit.html', {'wordlist': wordlist})
        
        if not csv_content.strip():
            messages.error(request, 'CSVコンテンツを入力してください。')
            return render(request, 'wordlists/edit.html', {'wordlist': wordlist})
        
        # Validate CSV format
        errors = validate_csv_format(csv_content)
        if errors:
            for error in errors:
                messages.error(request, f'CSV形式エラー: {error}')
            return render(request, 'wordlists/edit.html', {'wordlist': wordlist})
        
        try:
            wordlist.name = name
            wordlist.description = description
            wordlist.csv_content = csv_content
            wordlist.is_shared = is_shared
            wordlist.save()
            
            if csv_file:
                wordlist.csv_file.save(csv_file.name, csv_file)
            
            messages.success(request, 'ワードリストが更新されました。')
            return redirect('wordlists:detail', pk=wordlist.pk)
            
        except Exception as e:
            messages.error(request, f'更新中にエラーが発生しました: {str(e)}')
    
    return render(request, 'wordlists/edit.html', {'wordlist': wordlist})


@login_required
def wordlist_delete(request, pk):
    """Delete a word list."""
    wordlist = get_object_or_404(WordList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        wordlist.delete()
        messages.success(request, 'ワードリストが削除されました。')
        return redirect('wordlists:list')
    
    return render(request, 'wordlists/delete.html', {'wordlist': wordlist})


@login_required
def wordlist_download(request, pk):
    """Download word list as CSV file."""
    wordlist = get_object_or_404(WordList, pk=pk)
    
    # Check access permissions
    if wordlist.user != request.user:
        if not wordlist.is_shared or not SharedWordList.objects.filter(
            wordlist=wordlist, user=request.user
        ).exists():
            messages.error(request, 'このワードリストにアクセスする権限がありません。')
            return redirect('wordlists:list')
    
    response = HttpResponse(wordlist.csv_content, content_type='text/csv; charset=utf-8')
    filename = f"{wordlist.name}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@method_decorator(csrf_exempt, name='dispatch')
class WordListAPIView(View):
    """API view for word list operations."""
    
    def post(self, request):
        """Create a new word list via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            name = data.get('name', '')
            description = data.get('description', '')
            csv_content = data.get('csv_content', '')
            
            if not name or not csv_content:
                return JsonResponse({'error': 'name and csv_content are required'}, status=400)
            
            # Check if name already exists
            if WordList.objects.filter(user=request.user, name=name).exists():
                return JsonResponse({'error': 'Word list with this name already exists'}, status=400)
            
            # Validate CSV format
            errors = validate_csv_format(csv_content)
            if errors:
                return JsonResponse({'error': 'CSV format errors', 'details': errors}, status=400)
            
            wordlist = WordList.objects.create(
                user=request.user,
                name=name,
                description=description,
                csv_content=csv_content
            )
            
            return JsonResponse({
                'id': wordlist.pk,
                'name': wordlist.name,
                'description': wordlist.description,
                'word_count': wordlist.word_count,
                'created_at': wordlist.created_at.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get word list data via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        wordlists = WordList.objects.filter(user=request.user)
        data = []
        
        for wordlist in wordlists:
            data.append({
                'id': wordlist.pk,
                'name': wordlist.name,
                'description': wordlist.description,
                'word_count': wordlist.word_count,
                'is_shared': wordlist.is_shared,
                'is_active': wordlist.is_active,
                'created_at': wordlist.created_at.isoformat(),
                'updated_at': wordlist.updated_at.isoformat()
            })
        
        return JsonResponse({'wordlists': data})