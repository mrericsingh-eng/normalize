import re
from typing import List


def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and converting to lowercase."""
    return re.sub(r'\s+', ' ', text.strip().lower())


def extract_phone_digits(phone: str) -> str:
    """Extract only digits from phone number."""
    return re.sub(r'\D', '', phone)


def is_valid_email(email: str) -> bool:
    """Check if email format is valid."""
    pattern = r'[\w\.\+\-]+@[\w\.\-]+\.\w+'
    return bool(re.match(pattern, email))


def is_valid_zip(zip_code: str) -> bool:
    """Check if ZIP code is valid US 5-digit format."""
    return bool(re.match(r'^\d{5}$', zip_code))
