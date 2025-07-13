"""
API URL configuration for the api app.
"""
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import sys
import os

# Add processing module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

app_name = 'api'

@csrf_exempt
def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Teams Transcript Cleaner API is running',
        'version': '1.0.0'
    })

@csrf_exempt
def api_info(request):
    """API information endpoint."""
    return JsonResponse({
        'api_name': 'Teams Transcript Cleaner API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'transcripts': '/api/v1/transcripts/',
            'corrections': '/api/v1/corrections/',
            'wordlists': '/api/v1/wordlists/',
        }
    })

@csrf_exempt
def check_api_key(request):
    """Check OpenAI API key status."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    openai_api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    
    if not openai_api_key:
        return JsonResponse({
            'status': 'missing',
            'message': 'OpenAI API key not configured'
        })
    
    # Simple validation - check if key looks like a valid format
    if openai_api_key.startswith('sk-') and len(openai_api_key) > 20:
        return JsonResponse({
            'status': 'valid',
            'message': 'API key is configured'
        })
    else:
        return JsonResponse({
            'status': 'invalid',
            'message': 'API key format appears invalid'
        })

@csrf_exempt
def execute_correction(request):
    """Execute text correction."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        input_text = data.get('input_text', '')
        processing_mode = data.get('processing_mode', 'misspelling')
        model = data.get('model', 'gpt-4o')
        custom_prompt = data.get('custom_prompt', '')
        csv_content = data.get('csv_content', '')
        
        if not input_text:
            return JsonResponse({'error': 'Input text is required'}, status=400)
        
        # Import processing modules
        try:
            from processing.openai_service import correct_text, estimate_cost
            from processing.csv_parser import parse_csv_text
        except ImportError as e:
            return JsonResponse({'error': f'Processing module not found: {str(e)}'}, status=500)
        
        # Parse CSV if provided
        correction_words = []
        if csv_content and processing_mode == 'misspelling':
            try:
                correction_words = parse_csv_text(csv_content)
            except Exception as e:
                return JsonResponse({'error': f'CSV parsing error: {str(e)}'}, status=400)
        
        # Estimate cost first
        try:
            estimated_cost = estimate_cost(input_text, model)
        except Exception as e:
            return JsonResponse({'error': f'Cost estimation failed: {str(e)}'}, status=500)
        
        # Check user's budget
        if hasattr(request.user, 'total_api_cost') and hasattr(request.user, 'api_usage_limit'):
            current_cost = float(request.user.total_api_cost)
            usage_limit = float(request.user.api_usage_limit)
            if current_cost + estimated_cost > usage_limit:
                return JsonResponse({
                    'error': 'Insufficient API budget',
                    'estimated_cost': estimated_cost,
                    'remaining_budget': usage_limit - current_cost
                }, status=402)
        
        # Execute correction
        try:
            corrected_text, actual_cost, input_tokens, output_tokens = correct_text(
                processing_mode=processing_mode,
                user_custom_prompt=custom_prompt,
                input_text=input_text,
                correction_words=correction_words,
                model=model
            )
            
            # Update user's API usage (if UserProfile exists)
            try:
                if hasattr(request.user, 'total_api_cost'):
                    from decimal import Decimal
                    current_cost = request.user.total_api_cost
                    new_cost = current_cost + Decimal(str(actual_cost))
                    request.user.total_api_cost = new_cost
                    request.user.save()
            except Exception as user_update_error:
                # Continue anyway - user cost update failure shouldn't break the response
                pass
            
            return JsonResponse({
                'success': True,
                'corrected_text': corrected_text,
                'cost': actual_cost,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'estimated_cost': estimated_cost
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Correction failed: {str(e)}'}, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


urlpatterns = [
    path('health/', health_check, name='health'),
    path('info/', api_info, name='info'),
    path('check-api-key/', check_api_key, name='check_api_key'),
    path('corrections/execute/', execute_correction, name='execute_correction'),
]