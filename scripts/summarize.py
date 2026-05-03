"""Summarize papers with Gemini Flash."""

import json
import time

from google import genai

PROMPT = """You are a technical assistant for a machine learning engineer specializing in \
Vision-Language-Action (VLA) models and robot learning.

Analyze the paper below and return a JSON object with exactly these five fields:
{{
  "one_liner": "Core contribution in one sentence, max 20 words.",
  "problem": "Specific challenge addressed. 1-2 sentences, concrete.",
  "approach": "Key technical idea or method. 2-3 sentences, technical but clear.",
  "result": "Main result or finding with numbers if available. 1-2 sentences.",
  "relevance": "Why a VLA/robot-learning engineer should care. 1-2 sentences."
}}

Rules:
- Be direct and technical. No fluff like "the authors propose" or "this paper presents".
- Return only valid JSON. No markdown fences.

Title: {title}
Abstract: {abstract}"""


def _call_with_retry(client, model_name: str, prompt: str, paper: dict) -> dict:
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            return json.loads(text)
        except Exception as e:
            msg = str(e)
            if "429" in msg and attempt < 2:
                wait = 45 * (attempt + 1)
                print(f"  [WARN] Rate limited, retrying in {wait}s…", flush=True)
                time.sleep(wait)
            else:
                print(
                    f"  [WARN] Gemini failed for '{paper['title'][:60]}': {e}",
                    flush=True,
                )
                return {
                    "one_liner": paper["title"],
                    "problem": "Summary unavailable.",
                    "approach": paper["abstract"][:400] + "…",
                    "result": "",
                    "relevance": "",
                }


def summarize_papers(papers: list[dict], api_key: str, model_name: str) -> list[dict]:
    client = genai.Client(api_key=api_key)

    for paper in papers:
        prompt = PROMPT.format(title=paper["title"], abstract=paper["abstract"])
        paper["summary"] = _call_with_retry(client, model_name, prompt, paper)
        time.sleep(4)  # stay well within free-tier rate limit (15 RPM)

    return papers
