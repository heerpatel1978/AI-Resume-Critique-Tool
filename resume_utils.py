import fitz  # PyMuPDF
import language_tool_python
import re
from collections import Counter
from dateutil import parser
from datetime import datetime

# Initialize tools and data
tool = language_tool_python.LanguageTool('en-US')

# Load stopwords
stopwords = set(open('stopwords.txt').read().split())

# Predefined data
# skills known
all_skills = {
    "Python", "Java", "C++", "C", "SQL", "NoSQL", "HTML", "CSS", "JavaScript",
    "Machine Learning", "Deep Learning", "Data Science", "Flask", "Django",
    "Streamlit", "Pandas", "Numpy", "Matplotlib", "Seaborn", "Keras", "Tensorflow",
    "Scikit-learn", "Linux", "Windows", "Git", "Github", "Data Analytics",
    "Computer Vision", "Natural Language Processing", "OpenCV", "AWS", "Azure",
    "Big Data", "Tableau", "Power BI", "R", "Hadoop", "Spark", "Data Mining",
    "Data Visualization", "Communication", "Teamwork", "Leadership", "Presentation"
}

# common sections
ATS_SECTIONS = ["education", "experience", "skills", "projects", "certifications", "summary",
                "contact", "profile", "objective", "professional summary"]

# skill targets 
skill_targets = {
        "Data Science Jobs": ["Data Visualization", "Predictive Analysis", "Statistical Modeling", "Data Mining", "Clustering & Classification", "Data Analytics", "Quantitative Analysis", "Web Scraping", "ML Algorithms", "Keras", "Pytorch", "Probability", "Scikit-learn", "Tensorflow", "Flask", "Streamlit"],
        "Web Development Jobs": ["HTML", "CSS", "JavaScript", "React", "Flask", "Django", "Bootstrap", "Web Development"],
        "Software Developer Jobs": ["C++", "Java", "Python", "Data Structures", "OOP", "Algorithms", "Software Engineering"],
        "Machine Learning Jobs": ["Machine Learning", "Deep Learning", "Scikit-learn", "Keras", "Tensorflow", "Pytorch", "Data Preprocessing"],
        "Cloud / DevOps Jobs": ["AWS", "Azure", "Docker", "Kubernetes", "CI/CD", "DevOps", "Cloud Computing"],
        "UI/UX Designer Jobs": ["Figma", "Adobe XD", "UI Design", "UX Research", "Wireframe", "Prototyping"]
    }

# --- Utility Extraction Functions ---
# For text
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return doc, "".join(page.get_text() for page in doc)

# For name and email
def extract_name_email(text):
    name = next((l.title() for l in text.splitlines() if l.strip() and len(l.split()) >= 2 and not re.search(r'\d', l)), "Name Not Found")
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return name, email.group() if email else "Email Not Found"

# For grammer check
def grammar_check(text):
    return tool.check(text)

# For known skills
def extract_skills(text):
    resume_words = set(w.lower() for w in re.findall(r'\b\w+\b', text))
    matched = [skill for skill in all_skills if skill.lower() in resume_words]
    return matched

# For Level
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

# Predict job role
def detect_job_role(text):  
    text_lower = text.lower()
    scores = {role: sum(1 for kw in kws if kw in text_lower) for role, kws in skill_targets.items()}
    predicted_role = max(scores, key=scores.get)
    return predicted_role if scores[predicted_role] > 1 else "General IT Jobs"

# Compare resume skill against role
def match_skills(resume_skills, target_skills):
    matched = list(set(resume_skills).intersection(set(target_skills)))
    unmatched = list(set(target_skills) - set(resume_skills))
    return matched, unmatched

# For ATS Score
# To check section
def check_sections(text):
    found = set()
    for section in ATS_SECTIONS:
        if section in text.lower():
            found.add(section)
    return len(found), list(found)

# For image and symbol check
def detect_bad_ats_elements(doc):
    for page in doc:
        if page.get_images(): return 1
        if len(re.findall(r'[^\w\s,.:\-\(\)]', page.get_text())) > 20:
            return 1
    return 0

# ATS evaluation
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
    target_skills = skill_targets.get(job_target, [])
    matched_skills, missing_skills = match_skills(resume_skills, target_skills)
    grammar_issues = grammar_check(resume_text)
    user_level = get_user_level(resume_text)
    ats_score, ats_tips = compute_ats_score( resume_text, doc, resume_skills, target_skills, grammar_issues, name, email)

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
