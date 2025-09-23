# Normalize-Bot API

A travel message normalization API that classifies urgency, extracts contact information and travel entities, detects typos, and enriches responses with emergency numbers.

## Overview

This API processes travel advisor messages to:
- **Classify** message urgency (urgent/high_risk/base)
- **Extract** contact information (names, phones, emails, addresses)
- **Extract** travel entities (cities, countries, hotels, restaurants)
- **Detect** typos in cities, countries, phone numbers, and ZIP codes
- **Enrich** with local emergency numbers for mentioned locations

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Option 1: Docker (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/normalize-bot.git
cd normalize-bot
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env file and add your OpenAI API key
```

3. **Run with Docker:**
```bash
docker build -t normalize-bot .
docker run -p 8080:8080 --env-file .env normalize-bot
```

### Option 2: Local Development

1. **Clone and setup:**
```bash
git clone https://github.com/your-username/normalize-bot.git
cd normalize-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env file and add your OpenAI API key
```

3. **Start the server:**
```bash
python src/app.py
```

The API will be available at `http://localhost:8080`

### Test the API

```bash
curl -X POST "http://localhost:8080/normalize" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test-123",
    "text": "Hi, I am in Seatlee and lost my passport. Call me at 661248083!"
  }'
```

## API Endpoints

### POST /normalize
Processes travel messages and returns normalized data.

### GET /healthz
Health check endpoint that returns `{"status": "ok"}`.

### Sample Response

```json
{
  "message_id": "test-123",
  "category": "urgent",
  "contact": {
    "first_name": "Alex",
    "last_name": "Smith",
    "email": null,
    "phone": "9175551234",
    "zip": "10003"
  },
  "entities": [
    {"type": "city", "value": "seattle"},
    {"type": "city", "value": "rome"}
  ],
  "enrichment": {
    "local_emergency_numbers": ["911", "112"],
    "city_typo": "seatlee -> seattle",
    "country_typo": null,
    "phone_number_typo": "661248083",
    "zip_code_typo": null
  }
}
```

## Classification Types

- **urgent**: Immediate assistance needed (lost documents, emergencies)
- **high_risk**: Safety concerns, time-sensitive issues
- **base**: General travel planning, routine requests

## Entity Types

- **city**: Cities, towns (e.g., "Rome", "NYC", "Seattle")
- **country**: Countries, nations (e.g., "South Africa", "Mexico")
- **hotel**: Hotels, resorts (e.g., "Marriott", "Chapter Roma")
- **restaurant**: Restaurants, cafes (e.g., "Olive Garden", "McDonald's")

## Typo Detection

Automatically detects and suggests corrections for:
- **city_typo**: "Seatlee" → "seattle"
- **country_typo**: "Mexco" → "mexico"
- **phone_number_typo**: Wrong digit count (9 or 11+ digits)
- **zip_code_typo**: Non-5-digit ZIP codes

## Testing

### Run All Test Cases
```bash
python test_final_json_output.py
```

### Quick Requirements Test
```bash
python test_requirements_quick.py
```

### Full Production Requirements Test
```bash
python test_requirements.py
```

## Production Requirements

This API meets the following production standards:

- **Latency**: p95 ≤ 20 seconds
- **Stability**: < 1% non-2xx responses (tested with 200 sequential requests)
- **Error Handling**: Informative JSON error responses
- **Security**: Secrets only via environment variables

## Architecture

### Core Components

- **FastAPI** web framework for high-performance async API
- **OpenAI GPT-4o-mini** for intelligent text processing
- **Pydantic** models for data validation
- **Geocoding APIs** for location validation
- **Emergency number APIs** for safety enrichment

### Key Features

- **LLM-based processing** for maximum accuracy
- **Integrated typo detection** (no redundant API calls)
- **Hybrid geocoding** (API + static mappings for reliability)
- **Async/await** patterns for optimal performance
- **Comprehensive error handling** with fallback mechanisms

## File Structure

```
src/
├── app.py                    # Main FastAPI application
├── models.py                 # Pydantic data models
└── logic/
    ├── categorizer.py        # Message classification
    ├── extract_contact.py    # Contact extraction
    ├── extract_entities.py   # Entity extraction + typo detection
    ├── enrich.py            # Emergency number enrichment
    └── text_utils.py        # Text utilities

test_requirements.py         # Production requirements validation
test_requirements_quick.py   # Quick requirements test
test_final_json_output.py    # Comprehensive test cases
```

## Error Handling

All API errors return structured JSON responses:

```json
{
  "error": "Validation Error",
  "detail": "Missing required field: text"
}
```

Common error scenarios:
- Missing required fields
- Invalid JSON format
- OpenAI API failures (with fallback processing)
- Geocoding service unavailable (with static mappings)

## Public Deployment

### Deploying to Cloud Platforms

**Heroku:**
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_openai_api_key_here
git push heroku main
```

**Railway:**
```bash
# Install Railway CLI and login
railway new
railway add
railway run --service normalize-bot
```

**Google Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/normalize-bot
gcloud run deploy --image gcr.io/PROJECT-ID/normalize-bot --platform managed
```

### Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional (with defaults):
- `GEOCODER_URL`: Geocoding service URL
- `EMERGENCY_API_BASE`: Emergency numbers API base URL

### Public Demo

You can test the live API at: `https://your-deployed-url.herokuapp.com`

Sample curl command:
```bash
curl -X POST "https://your-deployed-url.herokuapp.com/normalize" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "demo-123",
    "text": "Hi, I am in Seatlee and lost my passport. Call me at 661248083!"
  }'
```

## Contributing

1. Follow existing code patterns and async/await usage
2. Update tests when adding new functionality
3. Ensure all production requirements continue to pass
4. Use environment variables for any external service credentials

## Support

For issues or questions:
1. Check the test outputs for debugging information
2. Verify OpenAI API key is correctly set
3. Ensure all dependencies are installed in the virtual environment
