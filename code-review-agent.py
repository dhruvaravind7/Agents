import json
import requests
from typing import Dict, Any

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

SYSTEM_INSTRUCTIONS = f"""
You are an agent responsible for reviewing code and error checking.
Be accurate, precise, and concise.
Never be rude. Pay attention to detail.
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
    return (r.json()["response"])

def ask_optional_clarifier(user_input : str) -> str:
    # If a clarifying question is neccessary ask it.
    prompt = f"""
    User Input: {user_input}
    Check the input and determine if more information is needed (coding language, what code is supposed to do).
    Output only ONE option:
        - ONLY If information is needed to check over the code, ask for the missing information using the format 'Can you provide {{missing information}}'.
            Example: If you do not know what langauge the code is in ask "Can you provide the what language you are coding in?"
            No additional statements should be made. Just a question asking for missing information.
        - IF NO INFORMATION IS NEEDED:
            output "NO_QUESTION"
    """
    
    resp = ollama_generate(prompt).strip()
    if ("NO_QUESTION" in resp or not "Can you provide" in resp):
        return ""
    return resp

def check_correctness(user_input, clarify) -> str:
    print("------Checking Correctness------\n")
    prompt = f"""
    You are a code correctness checker. Analyze the code below directly yourself.

    User Input: {user_input}
    Clarifier (May be empty): {clarify}

    Check for bugs, logic errors, and edge case failures. DO NOT check for syntax errors.
    DO NOT write any code. DO NOT suggest a function or script. DO NOT add preamble or explanation outside the format below.
    Analyze the code yourself and report what you find.

    ONLY PERMITTED OUTPUTS:
        If there are no errors at all, output exactly: No errors found
        Otherwise, FOR EVERY ERROR, output:
            "Line 5: {{line of code}}
                Explanation of what is wrong.
                Fix: {{correct line of code}}
            "
    """
    return ollama_generate(prompt).strip()

def check_syntax(user_input, clarify) -> str:
    print("------Checking Syntax------\n")
    prompt = f"""
    You are a syntax checker. Analyze the code below directly yourself.

    User Input: {user_input}
    Clarifier (May be empty): {clarify}

    DO NOT write any code. DO NOT suggest a function or script.
    Analyze the code yourself and report what you find. Double check answers and look deeply. 

    ONLY PERMITTED OUTPUTS:
        If errors exist, provide the line where they are and solutions for fixing them using the format for each error:
        'Line 5: {{line of code}}
            Explanation of what is wrong.
            Fix: {{correct line of code}}
        '
        If no errors exist, output exactly: No errors found
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
    user_input = get_multiline_input("Input the code you want to check:\n", "END")
    #user_input = input("Input the code you want to check:\n")
    q = ask_optional_clarifier(user_input)
    clarify = ""
    if q != "":
        clarify = get_multiline_input(q, "END").strip()
    print("=======Code Checker=======\n")
    print(f"{check_syntax(user_input, clarify)}\n" )
    print(f"{check_correctness(user_input, clarify)}\n" )


if __name__ == "__main__":
    main()