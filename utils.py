
# chatbot/utils.py
import google.generativeai as genai
import os

def setup_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def get_bot_response(model, user_input):
    prompt = """
    You are a medical first aid assistant. Your role is to:
    1. Provide immediate, non-emergency first aid advice
    2. ALWAYS recommend seeking professional medical help
    3. Never provide definitive diagnoses
    4. Focus on temporary relief and immediate steps
    5. Clearly state if something requires immediate emergency care
    6. Be clear about your limitations as an AI assistant

    NOTE: Please do not give response to any other question which are not related to the medical situation of patient, give response like this bot is only for medical help etc.
    
    User's current concern: {user_input}
    """
    
    formatted_prompt = prompt.format(user_input=user_input)
    
    try:
        response = model.generate_content(formatted_prompt)
        return response.text
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."
