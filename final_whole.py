import streamlit as st
import google.generativeai as genai
import pdf2image
from PIL import Image
import io
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    """Configure Gemini API"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def get_poppler_path():
    """Get the poppler path"""
    possible_paths = [
        r"C:\poppler\Library\bin",
        r"C:\poppler\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler\bin",
        r"C:\poppler\poppler-24.08.0\Library\bin",
        os.path.join(os.getcwd(), "poppler", "Library", "bin"),
        os.path.join(os.getcwd(), "poppler", "bin")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, "pdftoppm.exe")):
                return path
    return None

def pdf_to_images(pdf_file, poppler_path=None):
    """Convert PDF to images"""
    try:
        pdf_bytes = pdf_file.read()
        if sys.platform.startswith('win'):
            if poppler_path is None:
                poppler_path = get_poppler_path()
            os.environ['PATH'] = poppler_path + os.pathsep + os.environ['PATH']
        
        images = pdf2image.convert_from_bytes(pdf_bytes, dpi=200, poppler_path=poppler_path)
        return images
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None

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

        Remember to:
        1. Use everyday language that anyone can understand
        2. Explain medical terms when they must be used
        3. Focus on what's most important for the patient to know
        4. Keep explanations brief but clear
        5. Highlight any urgent actions needed
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
                st.warning(f"Error processing an image: {str(e)}")
                continue

        # Combine all responses into a single analysis
        combined_analysis = combine_analyses(responses)
        return combined_analysis

    except Exception as e:
        st.error(f"Error in Gemini analysis: {str(e)}")
        return None

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

    # Create a comprehensive summary
    combined["summary"] = "Complete analysis of all report pages combined."
    return combined

def display_analysis(analysis):
    """Display the analysis in a structured format"""
    if not analysis:
        st.error("No analysis available")
        return

    # Test Results
    st.subheader("📊 Test Results")
    col1, col2 = st.columns(2)
    with col1:
        if analysis["test_results"]["key_findings"]:
            st.write("**Key Findings:**")
            for finding in analysis["test_results"]["key_findings"]:
                st.write(f"• {finding}")
    with col2:
        if analysis["test_results"]["abnormal_values"]:
            st.write("**Abnormal Values:**")
            for value in analysis["test_results"]["abnormal_values"]:
                st.write(f"⚠️ {value}")

    # Health Assessment
    st.subheader("🏥 Health Assessment")
    if analysis["health_assessment"]["overall_status"]:
        st.write(f"**Overall Status:** {analysis['health_assessment']['overall_status']}")
    if analysis["health_assessment"]["areas_of_concern"]:
        st.write("**Areas of Concern:**")
        for concern in analysis["health_assessment"]["areas_of_concern"]:
            st.write(f"• {concern}")

    # Recommendations
    st.subheader("💡 Recommendations")
    for category in ["immediate_actions", "follow_up_tests", "lifestyle_changes"]:
        if analysis["recommendations"][category]:
            st.write(f"**{category.replace('_', ' ').title()}:**")
            for item in analysis["recommendations"][category]:
                st.write(f"• {item}")

def main():
    st.set_page_config(page_title="Medical Report Analysis", layout="wide")
    st.title("Medical Report Analysis")

    # Configure Gemini
    model = configure_gemini()

    # Language selection
    language = st.selectbox("Select Language", ["English", "Hindi", "Gujarati"])

    # File upload
    uploaded_file = st.file_uploader("Upload Medical Report (PDF)", type=['pdf'])

    if uploaded_file:
        try:
            # Convert PDF to images
            with st.spinner("Processing PDF..."):
                images = pdf_to_images(uploaded_file)
                if not images:
                    st.error("Could not process the PDF. Please check the file.")
                    return

            # Analyze button
            if st.button("Analyze Report"):
                with st.spinner("Analyzing report..."):
                    # Get consolidated analysis
                    analysis = get_gemini_response(model, images, language)
                    if analysis:
                        # Display analysis
                        display_analysis(analysis)
                        
                        # Add download button
                        json_str = json.dumps(analysis, indent=2)
                        st.download_button(
                            label="📥 Download Analysis",
                            data=json_str,
                            file_name="medical_analysis.json",
                            mime="application/json"
                        )
                    else:
                        st.error("Could not generate analysis. Please try again.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()