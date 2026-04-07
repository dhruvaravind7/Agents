import json
import requests
from typing import Dict, Any

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

SYSTEM_INSTRUCTIONS = """
You are Study Buddy Agent.
Be practical and structured.
Never be rude. Keep responses compact.
When grading, be fair and explain mistakes briefly.
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
    r = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["response"]

def ask_optional_clarifier(user_goal: str) -> str:
    """
    Decide whether we need 1 clarifying question. If not needed, return "".
    """
    prompt = f"""
User goal: {user_goal}

Reply with ONLY one of:
- NO_QUESTION  (if the goal has enough detail to teach from)
- A single clarifying question ending in ?  (if a key detail is missing)

No preamble. No explanation. One line only.
"""
    resp = ollama_generate(prompt).strip()
    if "NO_QUESTION" in resp or not resp.endwith("?"):
        return ""
    # Keep it as a single line question
    return resp.splitlines()[0].strip()

def create_lesson(user_goal: str, clarifier_answer: str) -> str:
    prompt = f"""
Create a study response for this goal.

Goal: {user_goal}
Extra info (may be empty): {clarifier_answer}

Output sections in this exact order:
1) Plan (3-6 bullets)
2) Explanation (short)
3) Practice (3 questions)
4) Answers (with brief reasoning)
5) Quick Quiz (5 rapid-fire questions, NO answers)
"""
    return ollama_generate(prompt).strip()

def grade_answers(user_goal: str, quiz_questions: str, user_answers: str) -> str:
    prompt = f"""
You are grading a student's answers.

Topic/Goal: {user_goal}

Quiz questions:
{quiz_questions}

Student answers:
{user_answers}

Return:
- Score: X/5
- For each question: Correct/Incorrect + 1-2 sentence explanation
- A targeted mini-lesson (max 8 bullets) focused only on missed concepts
- 3 new practice questions (no answers)
"""
    return ollama_generate(prompt).strip()

def extract_quiz_block(lesson_text: str) -> str:
    """
    Simple extraction: grab everything after the line that contains 'Quick Quiz'
    """
    lines = lesson_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "quick quiz" in line:
            start = i
            break
    if start is None:
        # fallback: just return last ~12 lines
        return "\n".join(lines[-12:]).strip()
    return "\n".join(lines[start:]).strip()

def main():
    user_goal = input("What do you want to study? ").strip()

    q = ask_optional_clarifier(user_goal)
    clarifier_answer = ""
    if q:
        clarifier_answer = input(f"{q} ").strip()

    lesson = create_lesson(user_goal, clarifier_answer)
    print("\n=== STUDY BUDDY ===\n")
    print(lesson)

    quiz = extract_quiz_block(lesson)
    print("\n=== YOUR TURN: Answer the Quick Quiz (1-5). ===")
    print("Type your answers like: 1) ... 2) ... 3) ... etc.\n")
    user_answers = input("Your answers:\n").strip()

    feedback = grade_answers(user_goal, quiz, user_answers)
    print("\n=== FEEDBACK ===\n")
    print(feedback)

if __name__ == "__main__":
    main()