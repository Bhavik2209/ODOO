
# chatbot/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import setup_gemini, get_bot_response
import json

def chat_view(request):
    return render(request, 'chatbot/chat.html')

@csrf_exempt
def get_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('message', '')
            
            # Get bot response
            model = setup_gemini()
            bot_response = get_bot_response(model, user_input)
            
            return JsonResponse({
                'status': 'success',
                'response': bot_response
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })