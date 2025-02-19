import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# print(GEMINI_API_KEY)

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

file = st.file_uploader("Choose Resumes")

job_desc = st.file_uploader("Choose a job description")

if file and job_desc:
    st.write(file.name)
    resume = text_extractor(file)
    job_spec = text_extractor(job_desc)
    # st.write(text_extractor(file))

    prompt = f''' Analyze the resume to identify and categorize details into sections such as Headline, Work Experience, Education, Awards/Certifications, Technical Skills, and Areas of Expertise. Compare these details against the job requirements specified in the provided job description. Calculate a match percentage for each of the following categories: Technical Skills, Soft Skills, and Relevant Experience, based on the degree of alignment between the resume content and job specifications. Extract and list matched items within each category to demonstrate how well the resume aligns with the job criteria. Ensure that your analysis is thorough, highlighting both the matches and the overall suitability score, enabling efficient resume screening and candidate assessment for HR applications.
    ---

    [FORMAT]
    Follow the following format:

    [INPUT]
    resume: The user's complete resume document
    job_description: The complete job description for which the resume is being evaluated
    [OUTPUT]
    keywords: Extracted categories from the resume such as Headline, Work Experience(s), Education, Awards/Certifications, Technical Skills, Areas of Expertise
    skills_experience_match: Detailed breakdown of matching skills and experiences between the resume and job description
    percentage_scores: A breakdown of percentage scores for each category, evaluating the resume against the job description


    ---
    Use the following formulas to compute the match percentages:  

    Technical Skills Score (T)  
    T = (Matched Technical Skills / Total Required Technical Skills) * 100  

    Soft Skills Score (S)  
    S = (Matched Soft Skills / Total Required Soft Skills) * 100  

    Relevant Experience Score (E)  
    E = (Matched Experience Keywords / Total Experience Keywords) * 100  

    Overall Match Score (M)  
    M = (0.4 * T) + (0.3 * S) + (0.3 * E)  
    
    ---
    
    
    For the given inputs, first generate your reasoning and then generate the outputs.

    [INPUT]
    resume: {resume}
    job_description: {job_spec}

    [REASONING]
    my_reasoning: <Your careful and step-by-step reasoning before you return the desired outputs for the given inputs>

    [OUTPUT]
    keywords: <Your output here that matches the format of keywords>
    skills_experience_match: <Your output here that matches the format of skills_experience_match>
    percentage_scores: **Technical Skills Match:** <T>%  
  - **Soft Skills Match:** <S>%  
  - **Relevant Experience Match:** <E>%  
  - **Overall Suitability Score:** <M>%  

    
    '''

        
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )

    # Use the response as a JSON string.
    st.write(response.text)