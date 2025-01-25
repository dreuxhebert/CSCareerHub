import pandas as pd
import pdfplumber
from docx import Document

def process_pdf(file):
    extracted_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_data.append({'type': 'text', 'label': text})
    return pd.DataFrame(extracted_data)

def process_docx(file):
    doc = Document(file)
    extracted_data = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            extracted_data.append({'type': 'text', 'label': text})
    return pd.DataFrame(extracted_data)

def grade_resume(resume_df):
    score = 0

    # Check for Education
    if any('degree' in label.lower() for label in resume_df['label']):
        score += 20

    # Check for Experience
    if any('years of experience' in label.lower() for label in resume_df['label']):
        score += 30

    # Define Relevant Skills with Weights
    skill_weights = {
    # Programming Languages
    'sql': 8,
    'python': 10,
    'java': 7,
    'c++': 7,
    'javascript': 4,
    'typescript': 4,
    'ruby': 5,
    'php': 5,
    'r': 8,
    'matlab': 8,
    'swift': 6,
    'go': 7,
    'scala': 8,
    'kotlin': 6,

    # Machine Learning Frameworks & Libraries
    'scikit-learn': 15,
    'tensorflow': 15,
    'pytorch': 15,
    'keras': 12,
    'xgboost': 12,
    'lightgbm': 10,
    'statsmodels': 8,
    'nltk': 8,
    'spacy': 10,
    'opencv': 10,
    'huggingface': 12,
    'mlflow': 10,
    'weka': 8,
    'onnx': 10,

    # Data Analysis & Visualization Tools
    'pandas': 10,
    'numpy': 10,
    'matplotlib': 8,
    'seaborn': 8,
    'plotly': 8,
    'ggplot2': 8,
    'd3.js': 8,
    'tableau': 10,
    'power bi': 10,
    'excel': 5,
    'qlik': 8,
    'microsoft bi': 8,

    # Cloud Platforms
    'aws': 12,
    'azure': 12,
    'google cloud platform': 12,
    'ibm cloud': 10,
    'snowflake': 8,
    'databricks': 10,
    'oracle cloud': 8,

    # DevOps & CI/CD Tools
    'docker': 12,
    'kubernetes': 12,
    'jenkins': 10,
    'circleci': 8,
    'git': 10,
    'github actions': 8,
    'ansible': 8,
    'terraform': 10,
    'chef': 8,
    'puppet': 8,
    'elasticsearch': 10,

    # Web Development Frameworks & Libraries
    'flask': 10,
    'django': 10,
    'fastapi': 10,
    'rails': 8,
    'laravel': 8,
    'express': 10,
    'react': 12,
    'angular': 10,
    'vue.js': 10,
    'bootstrap': 5,
    'tailwind css': 6,
    'next.js': 10,
    'nuxt.js': 10,

    # Databases
    'mysql': 10,
    'postgresql': 10,
    'mongodb': 10,
    'sqlite': 8,
    'mariadb': 8,
    'firebase': 8,
    'redis': 8,
    'cassandra': 8,
    'neo4j': 10,
    'dynamodb': 10,

    # Big Data & ETL Tools
    'hadoop': 12,
    'spark': 12,
    'hive': 10,
    'kafka': 12,
    'airflow': 10,
    'datastage': 8,
    'talend': 8,
    'informatica': 10,
    'apache beam': 10,
    'flink': 10,

    # AI & NLP Tools
    'transformers': 15,
    'openai gpt': 15,
    'bert': 15,
    'lstm': 12,
    'gru': 12,
    't5': 12,
    'gpt-4': 15,
    'word2vec': 10,
    'fasttext': 10,
    'seq2seq': 10,

    # Software Development Tools
    'visual studio code': 5,
    'intellij': 6,
    'eclipse': 5,
    'pycharm': 6,
    'atom': 5,
    'netbeans': 5,
    'vim': 5,
    'sublime text': 5,
    'android studio': 8,
    'xcode': 8,

    # System & Network Tools
    'linux': 8,
    'unix': 8,
    'windows server': 6,
    'bash': 8,
    'active directory': 6,
    'nginx': 10,
    'apache': 10,
    'vpn': 5,
    'wireshark': 6,

    # Soft Skills
    'teamwork': 5,
    'communication': 5,
    'problem-solving': 5,
    'leadership': 5,
    'critical thinking': 5,
    'collaboration': 5,
    'innovation': 5,
    'creativity': 5,
    'strategic planning': 5,
    'decision-making': 5
}

    for skill in skill_weights:
        if resume_df['label'].str.lower().str.contains(skill).any():
            score += skill_weights[skill]

    if any('certification' in label.lower() for label in resume_df['label']):
        certifications_count = sum('certification' in label.lower() for label in resume_df['label'])
        score += min(certifications_count * 5, 15)

    if any('project' in label.lower() for label in resume_df['label']):
        projects_count = sum('project' in label.lower() for label in resume_df['label'])
        score += min(projects_count * 5, 20)

        # Assign Grade with Detailed Feedback
        if score >= 92:
            return ("A (Job Ready): This resume demonstrates strong qualifications and preparedness for "
                    "professional roles. The candidate has showcased significant technical expertise, relevant experience,"
                    " and a robust set of skills and certifications. Employers would likely consider this candidate a top-tier choice for job opportunities.")
        elif score >= 83:
            return ("B (Very Internship Ready): This resume highlights good technical abilities and relevant experience"
                    " suitable for internships. While there are minor gaps, the candidate demonstrates strong potential"
                    " to excel in an internship role and is close to being fully job-ready.")
        elif score >= 66:
            return ("C (Internship Ready): The resume shows foundational skills and experience that make the candidate "
                    "suitable for internships. However, the candidate would benefit from further refining their qualifications,"
                    " adding more hands-on experience, or expanding their skill set to improve their job-readiness.")
        elif score >= 51:
            return ("D (Getting There): The resume reflects a basic understanding of relevant skills and concepts but"
                    " lacks sufficient depth in experience or qualifications. Focus on building more projects, gaining "
                    "practical experience, or obtaining certifications to strengthen your profile.")
        else:
            return ("F (Not Ready): The resume indicates significant gaps in skills, experience, or qualifications."
                    " To improve, start by learning and practicing the core technical and professional skills required "
                    "for the desired roles. Building projects, pursuing certifications, and gaining practical experience will be crucial steps forward.")





