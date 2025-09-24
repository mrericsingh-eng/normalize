import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import uvicorn
from dotenv import load_dotenv

from .models import NormalizeIn, NormalizeOut, Contact, Entity, Enrichment
from .logic.categorizer import categorize
from .logic.extract_contact import extract_contact
from .logic.extract_entities import extract_entities
from .logic.enrich import enrich

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Normalize Bot API",
    description="Production-ready normalization API for travel messages",
    version="1.0.0"
)

# Environment variables
PORT = int(os.getenv("PORT", 8080))
GEOCODER_BASE_URL = os.getenv("GEOCODER_BASE_URL", "https://nominatim.openstreetmap.org")
EMERGENCY_API_BASE = os.getenv("EMERGENCY_API_BASE", "https://emergencynumberapi.com/api")
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "1.0"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
USER_AGENT = os.getenv("USER_AGENT", "normalize-bot/1.0 (contact@example.com)")


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"ok": True}


@app.post("/normalize")
async def normalize_message(request: NormalizeIn) -> NormalizeOut:
    """
    Normalize a travel message by extracting contact info, entities, and enrichment data.
    """
    try:
        # Extract contact information (now async)
        contact_data = await extract_contact(request.text)
        contact = Contact(**contact_data) if any(contact_data.values()) else None

        # Extract entities and get country mapping with typo detection
        entities_data, country_map, typo_data = await extract_entities(
            request.text,
            GEOCODER_BASE_URL,
            USER_AGENT,
            HTTP_TIMEOUT_SECONDS
        )
        entities = [Entity(**entity) for entity in entities_data] if entities_data else None

        # Categorize the message (now async)
        category = await categorize(request.text)
        
        # Enrich with additional data
        enrichment_data = await enrich(
            entities_data or [],
            country_map,
            EMERGENCY_API_BASE,
            USER_AGENT,
            HTTP_TIMEOUT_SECONDS
        )

        # Add typo detection (now included in entity extraction)
        enrichment_data.update(typo_data)

        enrichment = Enrichment(**enrichment_data) if any(enrichment_data.values()) else None
        
        # Build response
        response = NormalizeOut(
            message_id=request.message_id,
            category=category,
            contact=contact,
            entities=entities,
            enrichment=enrichment
        )
        
        return response
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error processing message {request.message_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "detail": "An internal error occurred"}
        )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=400,
        content={"error": "BadRequest", "detail": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "InternalError", "detail": "An unexpected error occurred"}
    )


if __name__ == "__main__":
  import os
  port = int(os.environ.get("PORT", 8080))
  uvicorn.run(app, host="0.0.0.0", port=port)
