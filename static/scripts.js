// Module 1: Upload Resume
document.getElementById("resumeForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("resumeFile");
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch("/upload-resume/", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  window.uploadedResumeText = data.extracted_text || "";

  document.getElementById("resumeOutput").textContent = JSON.stringify(data, null, 2);
});

// Module 2: Match Resume with Job Description
document.getElementById("matchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const jobDescription = document.getElementById("jobDescription").value;
  const resumeText = window.uploadedResumeText || "";

  if (!resumeText || !jobDescription) {
    alert("Please upload a resume and enter a job description.");
    return;
  }

  const res = await fetch("/match-resume/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      resume_text: resumeText,
      job_description: jobDescription
    })
  });

  const data = await res.json();
  document.getElementById("matchOutput").textContent = JSON.stringify(data, null, 2);
});

// Module 3: Search Jobs on Web
document.getElementById("jobSearchForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const jobTitle = document.getElementById("jobTitle").value.trim();
  const experience = document.getElementById("experience").value.trim();
  const location = document.getElementById("location").value.trim();
  const graduationYear = document.getElementById("graduationYear").value.trim();

  const formData = new FormData();
  formData.append("job_title", jobTitle);
  formData.append("experience", experience);
  formData.append("location", location);
  formData.append("graduation_year", graduationYear);

  try {
    const res = await fetch("/search-web-jobs/", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    document.getElementById("searchOutput").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    console.error("Error fetching jobs:", err);
    alert("Job search failed. See console for details.");
  }
});
