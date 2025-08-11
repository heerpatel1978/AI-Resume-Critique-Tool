import fitz  # PyMuPDF
import language_tool_python
import re
from collections import Counter
from dateutil import parser

# Initialize tools and data
tool = language_tool_python.LanguageTool('en-US')
stopwords = set(open('stopwords.txt').read().split())

all_skills = {
    "Python", "Java", "C++", "C", "SQL", "NoSQL", "HTML", "CSS", "JavaScript",
    "Machine Learning", "Deep Learning", "Data Science", "Flask", "Django",
    "Streamlit", "Pandas", "Numpy", "Matplotlib", "Seaborn", "Keras", "Tensorflow",
    "Scikit-learn", "Linux", "Windows", "Git", "Github", "Data Analytics",
    "Computer Vision", "Natural Language Processing", "OpenCV", "AWS", "Azure",
    "Big Data", "Tableau", "Power BI", "R", "Hadoop", "Spark", "Data Mining",
    "Data Visualization", "Communication", "Teamwork", "Leadership", "Presentation"
}
 role_keywords = {
        "Data Science Jobs": ["data science", "machine learning", "pandas", "numpy", "scikit-learn", "statistics", "matplotlib", "tensorflow", "data analysis"],
        "Web Development Jobs": ["html", "css", "javascript", "react", "frontend", "backend", "web development", "flask", "django"],
        "Software Developer Jobs": ["c++", "java", "object-oriented", "algorithms", "data structures", "software engineering"],
        "Machine Learning Jobs": ["deep learning", "neural network", "keras", "pytorch", "ml model", "training data"],
        "Cloud / DevOps Jobs": ["aws", "azure", "docker", "kubernetes", "ci/cd", "cloud computing", "devops"],
        "UI/UX Designer Jobs": ["figma", "adobe xd", "wireframe", "ui design", "ux research", "prototype", "user experience"]
    }

ATS_SECTIONS = ["education", "experience", "skills", "projects", "certifications", "summary",
                "contact", "profile", "objective", "professional summary"]

# --- Utility Extraction Functions ---

def clean_text(text):
    return re.sub(r'[^A-Za-z0-9.,:\-()\n ]+', '', text)

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return doc, "".join(page.get_text() for page in doc)

def extract_name(text):
    lines = text.strip().split('\n')
    for line in lines:
        if line.strip() and len(line.strip().split()) >= 2 and not re.search(r'\d', line):
            return line.strip().title()
    return "Name Not Found"

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else "Email Not Found"

def grammar_check(text):
    return tool.check(text)

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return Counter(keywords).most_common(20)

def extract_skills(text):
    resume_words = set(w.lower() for w in re.findall(r'\b\w+\b', text))
    matched = [skill for skill in all_skills if skill.lower() in resume_words]
    return matched

from dateutil import parser
import re

def extract_total_experience_months(text):
    # Normalize dashes and date range separators
    text = text.replace("–", "-").replace("—", "-").replace(" to ", "-")
    
    # Regex to capture full date ranges with month and year
    # Example matches: Jan 2018 - Dec 2020, February 2019 - Present
    date_range_regex = re.compile(
        r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
        r'Dec(?:ember)?)[ ]+\d{4})\s*-\s*((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|'
        r'Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
        r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[ ]+\d{4}|present|current)',
        re.IGNORECASE
    )

    total_months = 0
    matches = date_range_regex.findall(text)

    from datetime import datetime

    now = datetime.now()

    for start_str, end_str in matches:
        try:
            start_date = parser.parse(start_str)
            if end_str.lower() in ["present", "current"]:
                end_date = now
            else:
                end_date = parser.parse(end_str)
                
            # Calculate difference in months
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
            if months > 0:
                total_months += months
        except Exception as e:
            # Skip if parsing fails
            continue

    return total_months


def detect_job_role(text):
    text_lower = text.lower()
    scores = {role: sum(1 for kw in kws if kw in text_lower) for role, kws in role_keywords.items()}
    predicted_role = max(scores, key=scores.get)
    return predicted_role if scores[predicted_role] > 1 else "General IT Jobs"

def check_sections(text):
    found = set()
    for section in ATS_SECTIONS:
        if section in text.lower():
            found.add(section)
    return len(found), list(found)

def detect_bad_ats_elements(doc):
    bad_elements = 0
    images = 0
    for page in doc:
        if page.get_images():  # Images detected
            images = 1
        symbol_count = len(re.findall(r'[^\w\s,.:\-\(\)]', page.get_text()))
        if symbol_count > 20:
            bad_elements = 1
    return images or bad_elements

def match_skills(resume_skills, target_skills):
    matched = list(set(resume_skills).intersection(set(target_skills)))
    unmatched = list(set(target_skills) - set(resume_skills))
    return matched, unmatched

def get_user_level(text):
    total_months = extract_total_experience_months(text)

    if total_months > 0:
        years = total_months / 12
        if years < 1:
            return "Beginner"
        elif 1 <= years < 5:
            return "Intermediate"
        else:
            return "Advanced"
    else:
        return "Beginner"


def compute_ats_score(resume_text, doc, resume_skills, job_skills, grammar_issues, name, email):
    score = 0
    details = []

    # 1. Section presence (out of 20)
    section_count, found_sections = check_sections(resume_text)
    section_score = min(section_count, 7) * (20 / 7)
    score += section_score
    if section_score < 10:
        details.append("Add more standard ATS sections (Education, Skills, Experience, etc.).")

    # 2. Keyword match (out of 30)
    matched = set([skill.lower() for skill in resume_skills]) & set([skill.lower() for skill in job_skills])
    keyword_score = min(len(matched), 10) * 3  # Up to 30
    score += keyword_score
    if keyword_score < 15:
        details.append("Optimize resume with more job-specific keywords.")

    # 3. Readability/grammar (out of 15)
    grammar_penalty = min(len(grammar_issues), 10) * 1.5
    grammar_score = max(15 - grammar_penalty, 0)
    score += grammar_score
    if grammar_score < 10:
        details.append("Reduce spelling/grammar mistakes for ATS readability.")

    # 4. Contact info present (10)
    contact_score = 10 if name != 'Name Not Found' and email != 'Email Not Found' else 0
    score += contact_score
    if contact_score == 0:
        details.append("Add clear name and email in your resume header.")

    # 5. Bad ATS elements (25)
    bad_elements = detect_bad_ats_elements(doc)
    format_score = 25 if not bad_elements else 10
    score += format_score
    if format_score < 25:
        details.append("Remove images/symbols/tables for better ATS parsing.")

    return round(score), details

# --- Main Analysis Function ---

def analyze_resume(file, job_role=None):
    doc, resume_text = extract_text_from_pdf(file)
    name = extract_name(resume_text)
    email = extract_email(resume_text)
    resume_skills = extract_skills(resume_text)
    job_target = detect_job_role(resume_text)

    # Define skill targets for various jobs
    target_skills = role_keywords.get(job_target, [])

    matched_skills, missing_skills = match_skills(resume_skills, target_skills)
    grammar_issues = grammar_check(resume_text)
    user_level = get_user_level(resume_text)

    # ATS Score
    ats_score, ats_tips = compute_ats_score(
        resume_text, doc, resume_skills, target_skills, grammar_issues, name, email
    )

    return {
        "name": name,
        "email": email,
        "level": user_level,
        "skills_in_resume": resume_skills,
        "recommended_skills": missing_skills,
        "resume_tips": ats_tips,
        "ats_score": ats_score,
        "job_target": job_target
    }  
