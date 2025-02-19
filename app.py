import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from google import genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def text_extractor(uploaded_files):
    if uploaded_files.type == "application/pdf":
        reader = PdfReader(uploaded_files)
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif uploaded_files.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        doc = Document(uploaded_files)
        text = "\n".join([para.text for para in doc.paragraphs])
    else:
        text = ""
    return text

def parse_gemini_response(response_text):
    try:
        # Look for the JSON content within [OUTPUT] section
        output_match = re.search(r'\[OUTPUT\]\s*```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if not output_match:
            # If no [OUTPUT] section, try finding any JSON block
            output_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        
        if output_match:
            json_str = output_match.group(1)
            return json.loads(json_str)
        else:
            st.error("Could not find JSON content in response")
            st.write("Raw response:", response_text)
            return None

    except Exception as e:
        st.error(f"Error parsing response: {str(e)}")
        st.write("Raw response:", response_text)
        return None

file = st.file_uploader("Choose Resumes")
job_desc = st.file_uploader("Choose a job description")

if file and job_desc:
    st.write(file.name)
    resume = text_extractor(file)
    job_spec = text_extractor(job_desc)

    prompt = f'''Analyze the resume to identify and categorize details into sections such as Headline, Work Experience, Education, Awards/Certifications, Technical Skills, and Areas of Expertise. Compare these details against the job requirements specified in the provided job description. Calculate a match percentage for each of the following categories: Technical Skills, Soft Skills, and Relevant Experience, based on the degree of alignment between the resume content and job specifications.

    Use the following formulas to compute the match percentages:  
    Technical Skills Score (T) = (Matched Technical Skills / Total Required Technical Skills) * 100  
    Soft Skills Score (S) = (Matched Soft Skills / Total Required Soft Skills) * 100  
    Relevant Experience Score (E) = (Matched Experience Keywords / Total Experience Keywords) * 100  
    Overall Match Score (M) = (0.4 * T) + (0.3 * S) + (0.3 * E)  

    Provide the output in the following JSON format:

    [OUTPUT]
    ```json
    {{
        "keywords": {{
            "Headline": "candidate name",
            "Work Experience": ["experience1", "experience2"],
            "Education": ["education1", "education2"],
            "Awards/Certifications": ["award1", "award2"],
            "Technical Skills": ["skill1", "skill2"],
            "Areas of Expertise": ["area1", "area2"],
            "Soft Skills": ["soft1", "soft2"]
        }},
        "skills_experience_match": {{
            "Technical Skills": {{
                "Matched": ["skill1", "skill2"],
                "Explanation": "explanation text"
            }},
            "Soft Skills": {{
                "Matched": ["soft1", "soft2"],
                "Explanation": "explanation text"
            }},
            "Relevant Experience": {{
                "Matched": ["exp1", "exp2"],
                "Explanation": "explanation text"
            }}
        }},
        "percentage_scores": {{
            "Technical Skills Match": 75.5,
            "Soft Skills Match": 80.0,
            "Relevant Experience Match": 70.0,
            "Overall Suitability Score": 75.2
        }}
    }}
    ```

    [INPUT]
    resume: {resume}
    job_description: {job_spec}
    '''

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )

    # Get the response content and parse it
    response_text = response.text
    st.write("Raw response received. Parsing...")
    response_data = parse_gemini_response(response_text)

    if response_data:
        st.success("✅ Analysis Complete!")
        
        # Display Headline
        if 'keywords' in response_data:
            st.subheader("📝 Candidate Overview")
            st.markdown(f"**📌 Name:** {response_data['keywords']['Headline']}")
            
            # Display Work Experience
            if 'Work Experience' in response_data['keywords']:
                st.subheader("💼 Work Experience")
                for exp in response_data['keywords']['Work Experience']:
                    st.markdown(f"- {exp}")

            # Display Education
            if 'Education' in response_data['keywords']:
                st.subheader("🎓 Education")
                for edu in response_data['keywords']['Education']:
                    st.markdown(f"- {edu}")

            # Display Awards/Certifications
            if 'Awards/Certifications' in response_data['keywords']:
                st.subheader("🏆 Awards & Certifications")
                for award in response_data['keywords']['Awards/Certifications']:
                    st.markdown(f"- {award}")

            # Display Technical Skills
            if 'Technical Skills' in response_data['keywords']:
                st.subheader("🛠 Technical Skills")
                st.write(", ".join(response_data['keywords']['Technical Skills']))

            # Display Areas of Expertise
            if 'Areas of Expertise' in response_data['keywords']:
                st.subheader("📌 Areas of Expertise")
                st.write(", ".join(response_data['keywords']['Areas of Expertise']))

        # Display Match Scores
        if 'percentage_scores' in response_data:
            st.subheader("📊 Match Score Analysis")
            scores = response_data["percentage_scores"]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(label="🖥 Technical Skills", 
                       value=f"{scores['Technical Skills Match']:.1f}%")
            col2.metric(label="🤝 Soft Skills", 
                       value=f"{scores['Soft Skills Match']:.1f}%")
            col3.metric(label="📈 Experience", 
                       value=f"{scores['Relevant Experience Match']:.1f}%")
            col4.metric(label="🔥 Overall", 
                       value=f"{scores['Overall Suitability Score']:.1f}%")

        # Display Skills Match Analysis
        if 'skills_experience_match' in response_data:
            st.subheader("🔍 Skills & Experience Match")
            matches = response_data["skills_experience_match"]

            with st.expander("🖥 Technical Skills Match"):
                st.markdown("**✅ Matched Skills:**")
                st.write(", ".join(matches["Technical Skills"]["Matched"]))
                st.markdown(f"**ℹ️ Explanation:** {matches['Technical Skills']['Explanation']}")

            with st.expander("🤝 Soft Skills Match"):
                st.markdown("**✅ Matched Skills:**")
                st.write(", ".join(matches["Soft Skills"]["Matched"]))
                st.markdown(f"**ℹ️ Explanation:** {matches['Soft Skills']['Explanation']}")

            with st.expander("📈 Relevant Experience Match"):
                st.markdown("**✅ Matched Experience:**")
                st.write(", ".join(matches["Relevant Experience"]["Matched"]))
                st.markdown(f"**ℹ️ Explanation:** {matches['Relevant Experience']['Explanation']}")
    else:
        st.error("Unable to parse the response. Please try again.")