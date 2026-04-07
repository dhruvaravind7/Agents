import json
import requests
from typing import Dict, Any


OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

SYSTEM_INSTRUCTIONS = """You are a job application advisor. You will be given a resume and a job description.

Your responsibilities:
- Read the job description carefully to understand what the role requires
- Analyze the resume completely before responding
- Base all feedback strictly on what is in the resume and job description — do not invent experience or qualifications
- Be structured, specific, and actionable in all responses
- Be encouraging but honest about gaps
- Never give generic advice — every suggestion must reference the actual job or resume content
"""
def ollama_generate(prompt : str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": SYSTEM_INSTRUCTIONS,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }
    read = requests.post(OLLAMA_GENERATE_URL, json = payload, timeout = 180)
    read.raise_for_status()
    return(read.json()["response"])

def gaps(resume, job):
    prompt = f"""You are going to compare the resume to the job description and output skills/experiences that the resume does not contain but the job wants.
        Resume: {resume}
        Job Description: {job}
        Never ouput something as missing if the job does not require it. Never output things that are already in the resume. 
        Only output things that are relevant to the job description AND absent from the resume.
        For each gap, use this format:
            - Missing: {{skill or experience}}
              Why it matters: {{one sentence from the job description context}}
        If no gaps exist, output exactly: No significant gaps found
    """
    response = ollama_generate(prompt).strip()
    return response
    
def resume_tailoring(resume, job):
    prompt = f"""You are going to compare the resume to the job description and ouput specific sentences/bullet points that should be rewritten to match the job description
        Resume: {resume}
        Job Description: {job}
        Never generate new bullet points or create experiences that are not already present in the resume.
        Only rewrite things to make the language more compatible with the job
         For each rewrite, use this format:
            Original: {{original bullet point}}
            Rewritten: {{improved version}}
            Why: {{one sentence explanation}}
        If no rewrites are needed, output exactly: Resume language is already well aligned
    """
    response = ollama_generate(prompt).strip()
    return response

def cover_letter(resume, job, gaps):
    prompt = f"""Resume: {resume}
                 Job Description: {job}
                 Gaps: {gaps}
                 Generate a professional cover letter for this job application.
                 Rules:
                 - Highlight strong matches between the resume and job description
                 - Acknowledge 1-2 growth areas from the gaps without dwelling on them
                 - Do NOT invent experience or skills not present in the resume
                 - Around 200 words, professional tone
                 - Output the cover letter only, no preamble or explanation
                 """
    return ollama_generate(prompt).strip()

def questions(resume, job, gaps):
    prompt = f"""Resume: {resume}
                 Job Description: {job}
                 Gaps: {gaps}
                 Generate 3 interview questions the applicant might face.
                 - 2 questions targeting areas where the applicant has strong experience
                 - 1 question targeting a gap in their background
                 For each question use this format:
                    Q1: {{question}}
                    Type: Strength / Gap
                    Why: {{one sentence on why an interviewer would ask this}}
                 Output the questions only, no preamble.
                 """
    return ollama_generate(prompt).strip()

def get_multiline_input(prompt: str, sentinel: str = "END") -> str:
    print(prompt)
    print(f"(Type '{sentinel}' on a new line when done)")
    lines = []
    while True:
        line = input()
        if line.strip() == sentinel:
            break
        lines.append(line)
    return "\n".join(lines)

def main():
    file_path = input("Provide the file of the resume: ").strip()
    with open(file_path, "r") as f:
        resume = f.read()
    job = get_multiline_input("Paste the job description below:\n(Type 'END' on a new line when done)\n", "END")
    print("======Checking Resume======\n")
    missing = gaps(resume, job)
    print("-----Missing Skills/Experiences-----\n")
    print(f"{missing}\n")
    print("-----Resume Tailoring-----\n")
    print(f"{resume_tailoring(resume, job)}\n")
    print("-----Cover Letter-----\n")
    print(f"{cover_letter(resume, job, missing)}\n")
    print("-----Interview Questions-----\n")
    print(f"{questions(resume, job, missing)}\n")
    
if __name__ == "__main__":
    main()