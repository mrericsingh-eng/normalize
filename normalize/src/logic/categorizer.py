import asyncio
import json
import os
from typing import Literal
import httpx


async def categorize(text: str) -> Literal["urgent", "high_risk", "base"]:
    """
    Categorize text based on risk level and urgency using OpenAI API.

    Rules:
    1. high_risk: Safety, medical, legal, or fraud threats (takes precedence)
    2. urgent: Needs reply/action ≤24h with explicit time indicators
    3. base: None of the above
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    prompt = f"""Classify this travel advisor message into exactly one category: "urgent", "high_risk", or "base".

RULES:
- high_risk: Safety, medical, legal, or fraud threats regardless of timing. Examples: lost passport, hospital, police, arrested, scam, credit card stolen, medical emergency, kidnapped, visa denied
- urgent: Caller needs reply/action ≤24h. Look for explicit time windows like "today", "tonight", "tomorrow", "in two hours", "ASAP", "immediately", "first thing"
- base: None of the above (general questions, future planning)

IMPORTANT: If both urgent and high_risk apply, return "high_risk" (it takes precedence).

Message: "{text}"

Respond with ONLY the category name: urgent, high_risk, or base"""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 10
                }
            )
            response.raise_for_status()

            result = response.json()
            category = result["choices"][0]["message"]["content"].strip().lower()

            # Validate response
            if category in ["urgent", "high_risk", "base"]:
                return category
            else:
                # Fallback to base if unexpected response
                return "base"

    except Exception as e:
        # Fallback to simple keyword-based classification if API fails
        return _fallback_categorize(text)


def _fallback_categorize(text: str) -> Literal["urgent", "high_risk", "base"]:
    """Fallback classification using simple keyword matching."""
    text_lower = text.lower()

    # High-risk keywords
    high_risk_keywords = [
        "lost passport", "passport stolen", "wallet stolen", "credit card stolen",
        "hospital", "medical emergency", "police", "arrested", "kidnapped",
        "visa denied", "scam", "fraud", "stolen", "emergency"
    ]

    for keyword in high_risk_keywords:
        if keyword in text_lower:
            return "high_risk"

    # Urgent keywords
    urgent_keywords = [
        "today", "tonight", "tomorrow", "asap", "immediately",
        "urgent", "now", "first thing"
    ]

    for keyword in urgent_keywords:
        if keyword in text_lower:
            return "urgent"

    return "base"
