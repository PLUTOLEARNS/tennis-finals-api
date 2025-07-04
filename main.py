from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import logging
from tennis_scraper import TennisScraper
from models import TennisResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Tennis Finals API",
    description="REST API for Tennis Championship Final Results",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hosted version
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Allow all hosts for hosted version
)

scraper = TennisScraper()

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "message": "Tennis Finals API",
        "description": "Get Tennis Championship Final Results",
        "endpoints": {
            "wimbledon": "/wimbledon?year=YYYY"
        }
    }

@app.get("/wimbledon")
@limiter.limit("10/minute")
async def get_wimbledon_result(
    request: Request,
    year: int = Query(..., description="Year of tennis championship", ge=1877, le=2030)
):
    if year < 1877:
        raise HTTPException(status_code=400, detail="Tennis championships started in 1877")
    if year > 2030:
        raise HTTPException(status_code=400, detail="Invalid year")
    
    try:
        logger.info(f"Fetching tennis final data for year: {year}")
        result = await scraper.get_tennis_result(year)
        
        return {
            "year": result.year,
            "champion": result.champion,
            "runner_up": result.runner_up,
            "score": result.score,
            "sets": result.sets,
            "tiebreak": result.tiebreak
        }
    except Exception as e:
        logger.error(f"Error fetching data for year {year}: {str(e)}")
        raise HTTPException(
            status_code=404, 
            detail=f"Tennis final data not available for year {year}"
        )

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8080,
        access_log=False,
        server_header=False,
        date_header=False,
    )
