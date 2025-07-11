import re
import PyPDF2
import docx
import os

SKILL_KEYWORDS = [
    "python", "java", "c++", "sql", "mysql", "postgresql", "mongodb", "azure", "aws", "gcp",
    "html", "css", "javascript", "react", "nodejs", "angular", "vue", "flask", "django",
    "tensorflow", "pytorch", "keras", "sklearn", "scikit-learn", "machine learning",
    "deep learning", "data analytics", "data visualization", "power bi", "tableau", "excel",
    "nlp", "computer vision", "opencv", "fastapi", "pandas", "numpy", "matplotlib", "seaborn",
    "git", "github", "linux", "bash", "jira", "api", "rest", "oop", "agile", "scrum"
]

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_skills(text):
    text_lower = text.lower()
    found = [skill for skill in SKILL_KEYWORDS if skill in text_lower]
    return list(set(found))

def parse_resume(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext == '.docx':
        text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported file format"}

    email = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    phone = re.findall(r"\+?\d[\d\s]{8,}", text)
    skills = extract_skills(text)

    return {
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "skills": skills,
        "text": text
    }
