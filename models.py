from pydantic import BaseModel, Field

class TennisResult(BaseModel):
    year: int = Field(..., description="Year of the championship")
    champion: str = Field(..., description="Name of the champion")
    runner_up: str = Field(..., description="Name of the runner-up")
    score: str = Field(..., description="Final score of the match")
    sets: int = Field(..., description="Number of sets played")
    tiebreak: bool = Field(..., description="Whether any set had a tiebreak")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2021,
                "champion": "Novak Djokovic",
                "runner_up": "Matteo Berrettini",
                "score": "6–7(4–7), 6–4, 6–4, 6–3",
                "sets": 4,
                "tiebreak": True
            }
        }
