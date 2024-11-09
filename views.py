
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







from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import google.generativeai as genai
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
import json
import os
from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    """Configure Gemini API"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def pdf_to_images(pdf_file):
    """Convert PDF to images using PyMuPDF"""
    try:
        # Read PDF content
        pdf_bytes = pdf_file.read()
        
        # Open PDF document
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        images = []
        
        # Process each page
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            # Convert to image (300 DPI for good quality)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        
        pdf_document.close()
        return images
        
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def get_gemini_response(model, images, language):
    """Get consolidated analysis from Gemini for all images"""
    try:
        # Convert all images to byte arrays
        image_parts = []
        for image in images:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            image_parts.append({
                "mime_type": "image/png",
                "data": img_byte_arr.getvalue()
            })
        
        prompt = f"""
        Summarize the following medical report in {language} in a clear, concise and easy-to-understand way:

        Please analyze these medical report images and provide a simplified summary that a non-medical expert can understand.
        Focus on:
        1. Main medical issues or concerns
        2. Key findings from tests and examinations
        3. Treatment plan and next steps
        4. Important follow-up actions
        5. Use simple, plain language without technical terms

        Provide the response in this JSON format:
        {{
            "test_results": {{
                "key_findings": [
                    "List main test results in simple terms",
                    "Explain what each result means for health"
                ],
                "abnormal_values": [
                    "List any concerning results",
                    "Explain why they are important"
                ],
                "normal_values": [
                    "List healthy/normal results",
                    "Explain what's good about them"
                ]
            }},
            "health_assessment": {{
                "overall_status": "Simple explanation of overall health status",
                "areas_of_concern": [
                    "List main health concerns in simple terms",
                    "Explain why each is important"
                ],
                "positive_indicators": [
                    "List good health indicators",
                    "Explain why they're positive"
                ]
            }},
            "recommendations": {{
                "immediate_actions": [
                    "List urgent steps to take",
                    "Explain why they're important"
                ],
                "follow_up_tests": [
                    "List recommended future tests",
                    "Explain why they're needed"
                ],
                "lifestyle_changes": [
                    "List suggested lifestyle improvements",
                    "Explain how they will help"
                ]
            }},
            "summary": "A brief, simple explanation of the overall report in 2-3 sentences"
        }}
        """

        # Process each image and combine results
        responses = []
        for image_part in image_parts:
            try:
                response = model.generate_content([prompt, image_part])
                try:
                    json_response = json.loads(response.text)
                    responses.append(json_response)
                except json.JSONDecodeError:
                    cleaned_response = response.text.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:-3]
                    responses.append(json.loads(cleaned_response))
            except Exception as e:
                continue

        # Combine all responses into a single analysis
        combined_analysis = combine_analyses(responses)
        return combined_analysis

    except Exception as e:
        raise Exception(f"Error in Gemini analysis: {str(e)}")

def combine_analyses(responses):
    """Combine multiple analyses into one comprehensive report"""
    combined = {
        "test_results": {
            "key_findings": [],
            "abnormal_values": [],
            "normal_values": []
        },
        "health_assessment": {
            "overall_status": "",
            "areas_of_concern": [],
            "positive_indicators": []
        },
        "recommendations": {
            "immediate_actions": [],
            "follow_up_tests": [],
            "lifestyle_changes": []
        },
        "summary": ""
    }

    for response in responses:
        if not response:
            continue

        # Combine test results
        for category in ["key_findings", "abnormal_values", "normal_values"]:
            combined["test_results"][category].extend(
                response.get("test_results", {}).get(category, [])
            )

        # Update health assessment
        assessment = response.get("health_assessment", {})
        if assessment.get("overall_status"):
            combined["health_assessment"]["overall_status"] = assessment["overall_status"]
        combined["health_assessment"]["areas_of_concern"].extend(
            assessment.get("areas_of_concern", [])
        )
        combined["health_assessment"]["positive_indicators"].extend(
            assessment.get("positive_indicators", [])
        )

        # Combine recommendations
        for category in ["immediate_actions", "follow_up_tests", "lifestyle_changes"]:
            combined["recommendations"][category].extend(
                response.get("recommendations", {}).get(category, [])
            )

    # Remove duplicates while preserving order
    for category in combined["test_results"]:
        combined["test_results"][category] = list(dict.fromkeys(
            combined["test_results"][category]
        ))
    for category in combined["health_assessment"]:
        if isinstance(combined["health_assessment"][category], list):
            combined["health_assessment"][category] = list(dict.fromkeys(
                combined["health_assessment"][category]
            ))
    for category in combined["recommendations"]:
        combined["recommendations"][category] = list(dict.fromkeys(
            combined["recommendations"][category]
        ))

    combined["summary"] = "Complete analysis of all report pages combined."
    return combined

@csrf_exempt
def analyze_medical_report(request):
    """Django view function for medical report analysis"""
    if request.method == 'GET':
        return render(request, 'medical_report/upload.html')
    
    elif request.method == 'POST':
        try:
            # Get the PDF file and language from the request
            pdf_file = request.FILES.get('pdf_file')
            language = request.POST.get('language', 'English')
            
            if not pdf_file:
                return JsonResponse({'error': 'No PDF file provided'}, status=400)
            
            # Configure Gemini
            model = configure_gemini()
            
            # Convert PDF to images
            images = pdf_to_images(pdf_file)
            
            # Get analysis from Gemini
            analysis = get_gemini_response(model, images, language)
            
            return JsonResponse({
                'success': True,
                'analysis': analysis
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
