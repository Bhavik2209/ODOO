import google.generativeai as genai
import streamlit as st
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    return model

def load_chat_history():
    try:
        if os.path.exists('chat_history.json') and os.path.getsize('chat_history.json') > 0:
            with open('chat_history.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading chat history: {e}")
    return []

def save_chat_history(history):
    try:
        with open('chat_history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def get_bot_response(model, user_input, chat_history):
    # Context for the medical chatbot
    prompt = """
    You are a medical first aid assistant. Your role is to:
    1. Provide immediate, non-emergency first aid advice
    2. ALWAYS recommend seeking professional medical help
    3. Never provide definitive diagnoses
    4. Focus on temporary relief and immediate steps
    5. Clearly state if something requires immediate emergency care
    6. Be clear about your limitations as an AI assistant

    NOTE :  Please do not give reponse to any other question which are not related to the medical situation of patient, give response like this bot is only for medical help etc.
    Previous conversation context:
    {chat_context}
    
    User's current concern: {user_input}
    """
    
    # Format chat context
    chat_context = "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                             for msg in chat_history[-5:]])  # Include last 5 messages for context
    
    formatted_prompt = prompt.format(chat_context=chat_context, user_input=user_input)
    
    try:
        response = model.generate_content(formatted_prompt)
        return response.text
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."

def main():
    st.title("Medical First Aid Assistant")
    st.markdown("""
    ⚕️ **Important Notice:**
    - This bot provides basic first aid guidance only
    - Always seek professional medical help
    - In case of emergency, call your local emergency number immediately
    """)
    
    # Initialize session state for chat history if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    
    # API Key input (you might want to handle this more securely in production)
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        st.error("Please set your GOOGLE_API_KEY in the .env file")
        return
    
    try:
        model = setup_gemini(api_key)
        
        # Chat interface
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                st.caption(message["timestamp"])
        
        # User input
        user_input = st.chat_input("Describe your medical concern...")
        
        if user_input:
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.caption(current_time)
            
            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": current_time
            })
            
            # Get and display bot response
            with st.chat_message("assistant"):
                bot_response = get_bot_response(model, user_input, st.session_state.chat_history)
                st.write(bot_response)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.caption(current_time)
            
            # Add bot response to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": bot_response,
                "timestamp": current_time
            })
            
            # Save chat history
            save_chat_history(st.session_state.chat_history)
            
        # Clear chat history button
        if st.sidebar.button("Clear Chat History"):
            st.session_state.chat_history = []
            save_chat_history([])
            st.rerun()
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()