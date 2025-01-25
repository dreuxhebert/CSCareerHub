import re
import pandas as pd
import pdfplumber
from docx import Document

def normalize_text(text):
    """Remove special characters and normalize to lowercase."""
    return re.sub(r'[^a-zA-Z\s]', ' ', text).lower().strip()

def clean_and_split_text(text):
    """Clean text and split into individual words."""
    text = normalize_text(text)
    return text.split()

def process_pdf(file):
    extracted_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                cleaned_text = normalize_text(text)
                extracted_data.append({'type': 'text', 'label': cleaned_text})
    print("Extracted PDF Data (Cleaned):", [entry['label'] for entry in extracted_data])  # Debugging log
    return pd.DataFrame(extracted_data)

def process_docx(file):
    doc = Document(file)
    extracted_data = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            cleaned_text = normalize_text(text)
            extracted_data.append({'type': 'text', 'label': cleaned_text})
    print("Extracted DOCX Data (Cleaned):", [entry['label'] for entry in extracted_data])  # Debugging log
    return pd.DataFrame(extracted_data)

def recommend_jobs(resume_jobs):
    job_to_skills = {
        'Data Scientist': {'python', 'pandas', 'numpy', 'tensorflow', 'scikit-learn', 'sql', 'machine learning', 'ml'},
        'Software Developer': {'java', 'c++', 'javascript', 'react', 'django', 'flask', 'git'},
        'DevOps Engineer': {'docker', 'kubernetes', 'terraform', 'jenkins', 'linux', 'aws', 'azure'},
        'Web Developer': {'html', 'css', 'javascript', 'react', 'vue.js', 'bootstrap', 'flask', 'django'},
        'Cloud Engineer': {'aws', 'azure', 'google cloud platform', 'terraform', 'docker', 'kubernetes'},
        'Machine Learning Engineer': {'python', 'tensorflow', 'pytorch', 'scikit-learn', 'mlflow', 'keras'},
        'Business Analyst': {'excel', 'power bi', 'tableau', 'sql', 'data visualization'},
        'Cybersecurity Analyst': {'vpn', 'firewall', 'linux', 'wireshark', 'bash', 'encryption'},
    }
    extracted_skills = set()
    for label in resume_jobs['label']:
        # Clean and split each line into individual words
        words = clean_and_split_text(label)
        extracted_skills.update(words)  # Add all normalized words to the set

    # Filter extracted skills to keep only relevant ones
    relevant_skills = set()
    for role_skills in job_to_skills.values():
        relevant_skills.update(role_skills)
    matched_skills = extracted_skills & relevant_skills

    recommendations = []
    for job, skills in job_to_skills.items():
        match_score = len(matched_skills & skills) / len(skills) * 100
        if match_score > 0:
            recommendations.append((job, match_score))

    recommendations.sort(key=lambda x: x[1], reverse=True)

    print("Generated Recommendations:", recommendations)

    return recommendations if recommendations else []




