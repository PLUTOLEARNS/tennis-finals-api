# Tennis Finals API

A FastAPI-based REST API that extracts tennis championship final results from Wikipedia, focusing on major tournaments like Wimbledon.

## Features

- REST API endpoint: `GET /wimbledon?year=YYYY`
- Web scraping from Wikipedia
- Automatic tiebreak detection
- Structured JSON responses
- Error handling for missing data
- **Security features**: Rate limiting, input validation, CORS protection

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

API available at: `http://localhost:8080`

**Note:** This API scrapes publicly available Wikipedia data for educational purposes.

## API Endpoints

- `GET /` - API information
- `GET /wimbledon?year=YYYY` - Get tennis final result for specific year
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Example Response

```json
{
  "year": 2023,
  "champion": "Carlos Alcaraz",
  "runner_up": "Novak Djokovic",
  "score": "1–6, 7–6(8–6), 6–1, 3–6, 6–4",
  "sets": 5,
  "tiebreak": true
}
```

## Technical Implementation

- **FastAPI**: Modern web framework for building APIs
- **aiohttp**: Async HTTP client for faster web scraping
- **BeautifulSoup**: HTML parsing for web scraping
- **Pydantic**: Data validation and serialization
- **Two parsing strategies**: Infobox and results table parsing
- **Async processing**: Non-blocking HTTP requests for better performance
- **Security**: Rate limiting, input sanitization, CORS protection, request size limits

## Security Features

- **Rate Limiting**: 10 requests/minute for data endpoints
- **Input Validation**: Year range validation (1877-2030)
- **CORS Protection**: Restricts cross-origin requests
- **Request Size Limits**: Prevents memory exhaustion attacks
- **Error Sanitization**: No internal error exposure
- **Content Length Validation**: Protects against large payloads
- **Host Validation**: Only accepts requests from localhost

## Architecture

```
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── tennis_scraper.py      # Web scraping logic
└── requirements.txt     # Dependencies
```
