from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match_jobs(resume_text, job_descriptions, top_n=5):
    if not isinstance(job_descriptions, list) or not job_descriptions:
        return []

    docs = [resume_text] + job_descriptions
    vectorizer = TfidfVectorizer().fit_transform(docs)
    vectors = vectorizer.toarray()

    resume_vec = vectors[0]
    job_vecs = vectors[1:]

    scores = cosine_similarity([resume_vec], job_vecs)[0]
    ranked_jobs = sorted(
        zip(job_descriptions, scores),
        key=lambda x: x[1],
        reverse=True
    )
    return [{"job_description": job, "score": round(score, 3)} for job, score in ranked_jobs[:top_n]]

def match_resume_to_job(resume_text: str, job_description: str) -> float:
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, job_description])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    return round(float(similarity), 3)
