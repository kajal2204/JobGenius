from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
import os, shutil, requests, random
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
import uvicorn
from app.resume_parser import parse_resume
from app.job_matcher import match_jobs, match_resume_to_job

load_dotenv()

app = FastAPI()
# Allow CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

parsed_resume_data = {"text": "", "skills": []}


# ----------- Module 1: Upload Resume -----------
@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, "temp_resume.pdf")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = parse_resume(file_path)
    parsed_resume_data["text"] = result.get("text", "")
    parsed_resume_data["skills"] = result.get("skills", [])

    return {
        "message": "Resume parsed successfully",
        "extracted_text": parsed_resume_data["text"],
        "skills": parsed_resume_data["skills"]
    }


# ----------- Module 2: Match Resume to Job Description -----------
class MatchRequest(BaseModel):
    job_description: str
    resume_text: str

@app.post("/match-resume/")
async def match_resume(data: MatchRequest):
    resume_path = os.path.join(UPLOAD_DIR, "temp_resume.pdf")
    if not os.path.exists(resume_path):
        return {"error": "Please upload a resume first."}

    score = match_resume_to_job(resume_path, data.job_description)
    return {"match_score": score}


# ----------- Module 3: Search Jobs Across the Web -----------
@app.post("/search-web-jobs/")
async def search_web_jobs(
    experience: int = Form(...),
    location: str = Form(...),
    graduation_year: int = Form(...),
    job_title: str = Form("")
):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return {"error": "Missing SERPAPI_KEY in environment."}

    skills = parsed_resume_data.get("skills", [])
    if not skills:
        return {"error": "No skills extracted from resume. Upload resume first."}

    all_skills = skills[:]
    random.shuffle(all_skills)
    selected_skills = all_skills[:6]

    query_base = f"{job_title.strip()} {experience} years job {location} {' '.join(selected_skills)} graduation year {graduation_year} hiring OR careers OR job opening"

    site_groups = [
        ["naukri.com", "glassdoor.com", "unstop.com"],
        ["thejobcompany.in", "developers.turing.com"],
        ["careers.google.com", "careers.microsoft.com", "careers.infosys.com", "tcs.com", "capgemini.com", "amazon.jobs"],
        ["linkedin.com"]
    ]

    jobs = []
    seen = set()
    domain_priority = {
        "careers.google.com": 0, "careers.microsoft.com": 0, "careers.infosys.com": 0, "tcs.com": 0, "capgemini.com": 0,
        "amazon.jobs": 0, "naukri.com": 1, "glassdoor.com": 1, "unstop.com": 1,
        "thejobcompany.in": 2, "developers.turing.com": 2, "linkedin.com": 3
    }

    for sites in site_groups:
        site_filter = " OR ".join(f"site:{d}" for d in sites)
        query = f"{query_base} {site_filter}"

        for start in [0, 100]:
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": 100,
                "start": start
            }

            try:
                resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
                data = resp.json()

                if "organic_results" not in data:
                    continue

                for item in data.get("organic_results", []):
                    link = item.get("link")
                    title = item.get("title", "Untitled Job Post").strip()
                    snippet = item.get("snippet", "").lower()

                    if not link or link in seen:
                        continue

                    domain = urlparse(link).netloc.replace("www.", "")

                    if "linkedin.com" in domain:
                        if (
                            "linkedin.com/in/" in link or "/directory/" in link or
                            "/articles/" in link or not (
                                "/jobs/" in link or "/posts/" in link or any(kw in snippet for kw in [
                                    "we're hiring", "apply now", "join our team", "open position", "job alert"
                                ])
                            )
                        ):
                            continue

                    if any(domain.endswith(d) for d in sites):
                        jobs.append({
                            "title": title,
                            "source": domain,
                            "url": link
                        })
                        seen.add(link)

            except Exception as e:
                print(f"Error: {e}")
                continue

    jobs.sort(key=lambda j: (domain_priority.get(j["source"], 999), j["source"]))
    return {
        "job_title": job_title or "(not provided)",
        "experience": experience,
        "location": location,
        "graduation_year": graduation_year,
        "skills_used": selected_skills,
        "results": jobs
    }


# ----------- Serve Static Frontend -----------
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = Path("static/index.html")
    return index_file.read_text(encoding="utf-8")