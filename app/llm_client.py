import os
import json
import time
from groq import Groq

from dotenv import load_dotenv
from app.prompts import REVIEW_PROMPT
from google import genai

load_dotenv()

# Initialize clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def review_with_groq(diff: str) -> list[dict]:
    """Send diff to Groq and get review comments."""
    try:
        prompt = REVIEW_PROMPT.format(diff=diff)

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # lower = more consistent output
            max_tokens=2048
        )

        raw = response.choices[0].message.content.strip()
        return parse_llm_response(raw)

    except Exception as e:
        print(f"Groq failed: {e}")
        return None  # triggers fallback


def review_with_gemini(diff: str) -> list[dict]:
    try:
        prompt = REVIEW_PROMPT.format(diff=diff)
        response = client_gemini.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        raw = response.text.strip()
        return parse_llm_response(raw)
    except Exception as e:
        print(f"Gemini failed: {e}")
        return None


def parse_llm_response(raw: str) -> list[dict]:
    """
    Safely parse JSON from LLM response.
    LLMs sometimes wrap JSON in markdown code blocks — handle that.
    """
    try:
        # Strip markdown code blocks if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        parsed = json.loads(raw)

        # Validate it's a list
        if not isinstance(parsed, list):
            print("LLM returned non-list JSON")
            return []

        # Filter out any malformed items
        valid = []
        for item in parsed:
            if all(k in item for k in ["file", "line", "severity", "category", "message"]):
                valid.append(item)

        return valid

    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response as JSON: {e}")
        print(f"Raw response was: {raw[:200]}")
        return []


def review_diff(diff: str) -> list[dict]:
    """
    Main entry point. Try Groq first, fall back to Gemini.
    Chunks large diffs to stay within token limits.
    """
    MAX_DIFF_CHARS = 12000  # safe limit for free tier models

    # If diff is small enough, review in one shot
    if len(diff) <= MAX_DIFF_CHARS:
        return _review_single(diff)

    # Otherwise chunk it
    print(f"Large diff ({len(diff)} chars), chunking...")
    return _review_chunked(diff, MAX_DIFF_CHARS)


def _review_single(diff: str) -> list[dict]:
    """Review a single diff chunk."""
    result = review_with_groq(diff)

    if result is None:
        print("Groq unavailable, trying Gemini...")
        time.sleep(1)
        result = review_with_gemini(diff)

    if result is None:
        print("Both models failed.")
        return []

    return result


def _review_chunked(diff: str, chunk_size: int) -> list[dict]:
    """Split large diff into chunks and review each."""
    chunks = [diff[i:i+chunk_size] for i in range(0, len(diff), chunk_size)]
    all_issues = []

    for i, chunk in enumerate(chunks):
        print(f"Reviewing chunk {i+1}/{len(chunks)}...")
        issues = _review_single(chunk)
        all_issues.extend(issues)
        time.sleep(1)  # respect rate limits

    return all_issues