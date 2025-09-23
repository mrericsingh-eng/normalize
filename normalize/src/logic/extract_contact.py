import json
import os
import re
from typing import Dict, Optional
import httpx
from .text_utils import extract_phone_digits, is_valid_email, is_valid_zip


async def extract_contact(text: str) -> Dict[str, Optional[str]]:
    """
    Extract contact information from text using OpenAI API.

    Returns dict with keys: first_name, last_name, email, phone, zip
    Only includes fields that are found and valid.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    prompt = f"""Extract contact information from this travel advisor message. Return a JSON object with these fields:
- first_name: First name (string or null)
- last_name: Last name (string or null)
- email: Email address (string or null)
- phone: Phone number digits only (string or null)
- zip: US ZIP code (string or null)

RULES:
- For phone: extract digits only, remove all formatting (e.g., "(917) 555-1234" → "9175551234")
- For names: Extract names from ANY of these patterns:
  * "I'm John Smith" → first_name: "John", last_name: "Smith"
  * "I'm John" → first_name: "John"
  * "I'm Alex." → first_name: "Alex"
  * "This is Alex" → first_name: "Alex"
  * "My name is Sarah" → first_name: "Sarah"
  * "I am David" → first_name: "David"
- Handle titles properly:
  * "I am Mr. Smith" → first_name: null, last_name: "Smith"
  * "I am Mrs. Johnson" → first_name: null, last_name: "Johnson"
  * "I am Dr. Brown" → first_name: null, last_name: "Brown"
  * "I am Dr. Nalwa. Also known as Hari" → first_name: "Hari", last_name: "Nalwa"
  * Extract last names from titles (Mr./Mrs./Dr./Prof. + surname) AND first names from "also known as" or similar phrases
- For ZIP: only US 5-digit ZIP codes
- Set fields to null if not found

Examples:
- "Hi Fora, I'm Alex." → {{"first_name": "Alex", "last_name": null, ...}}
- "I'm John Smith" → {{"first_name": "John", "last_name": "Smith", ...}}
- "I am Mr. Smith" → {{"first_name": null, "last_name": "Smith", ...}}
- "I am Dr. Nalwa. Also known as Hari" → {{"first_name": "Hari", "last_name": "Nalwa", ...}}

Message: "{text}"

Return ONLY valid JSON:"""

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
                    "max_tokens": 150
                }
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # Parse JSON response (handle markdown code blocks)
            try:
                # Remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                contact_data = json.loads(content)

                # Validate and clean the extracted data
                cleaned_contact = {
                    "first_name": contact_data.get("first_name"),
                    "last_name": contact_data.get("last_name"),
                    "email": contact_data.get("email"),
                    "phone": contact_data.get("phone"),
                    "zip": contact_data.get("zip")
                }

                # Additional validation
                if cleaned_contact["email"] and not is_valid_email(cleaned_contact["email"]):
                    cleaned_contact["email"] = None

                if cleaned_contact["phone"]:
                    # Ensure phone is digits only
                    cleaned_contact["phone"] = extract_phone_digits(cleaned_contact["phone"])
                    if len(cleaned_contact["phone"]) != 10:
                        cleaned_contact["phone"] = None

                if cleaned_contact["zip"] and not is_valid_zip(cleaned_contact["zip"]):
                    cleaned_contact["zip"] = None

                return cleaned_contact

            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return _fallback_extract_contact(text)

    except Exception as e:
        # Fallback to regex-based extraction if API fails
        return _fallback_extract_contact(text)


def _fallback_extract_contact(text: str) -> Dict[str, Optional[str]]:
    """Fallback contact extraction using regex patterns."""
    result = {
        "first_name": None,
        "last_name": None,
        "email": None,
        "phone": None,
        "zip": None
    }

    # Extract names using simple heuristics
    names = _extract_names_fallback(text)
    if names:
        result["first_name"] = names[0]
        if len(names) > 1:
            result["last_name"] = names[1]

    # Extract email
    email = _extract_email_fallback(text)
    if email and is_valid_email(email):
        result["email"] = email

    # Extract phone
    phone = _extract_phone_fallback(text)
    if phone:
        result["phone"] = phone

    # Extract ZIP code
    zip_code = _extract_zip_fallback(text)
    if zip_code and is_valid_zip(zip_code):
        result["zip"] = zip_code

    return result


def _extract_names_fallback(text: str) -> Optional[list]:
    """Extract first and last name using heuristics."""
    patterns = [
        r'(?:I\'m|I am|This is)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)',
        r'(?:Hi|Hello|Hey)\s+[A-Za-z]+,\s*I\'m\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)',
        r'My name is\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return [match.group(1), match.group(2)]

    return None


def _extract_email_fallback(text: str) -> Optional[str]:
    """Extract email address."""
    pattern = r'[\w\.\+\-]+@[\w\.\-]+\.\w+'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def _extract_phone_fallback(text: str) -> Optional[str]:
    """Extract US-style phone number and return digits only."""
    patterns = [
        r'\((\d{3})\)\s*(\d{3})[-.]?(\d{4})',
        r'(\d{3})[-.](\d{3})[-.](\d{4})',
        r'(\d{3})\s+(\d{3})\s+(\d{4})',
        r'(\d{10})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                return extract_phone_digits(''.join(match.groups()))
            elif len(match.groups()) == 1:
                return extract_phone_digits(match.group(1))

    return None


def _extract_zip_fallback(text: str) -> Optional[str]:
    """Extract US 5-digit ZIP code."""
    pattern = r'\b(\d{5})\b'
    match = re.search(pattern, text)
    return match.group(1) if match else None
