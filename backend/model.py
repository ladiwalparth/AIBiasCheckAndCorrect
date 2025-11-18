from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    uri: str
    use_selenium: bool = False

class AnalyzeResult(BaseModel):
    summary: str
    overall_score: Optional[int] = None
    stereotyping_feedback: str
    stereotyping_score: int
    stereotyping_example: str
    representation_feedback: str
    representation_score: int
    representation_example: str
    language_feedback: str
    language_score: int
    language_example: str
    framing_feedback: str
    framing_score: int
    framing_example: str
    positive_aspects: str
    improvement_suggestions: str
    male_to_female_mention_ratio: float
    gender_neutral_language_percentage: float

    # --- NEW FIELDS ---
    # Sentiment analysis (0-100) and label
    sentiment_score: Optional[float] = None                 # 0..100
    sentiment_label: Optional[str] = None                 # "Positive" / "Neutral" / "Negative"

    # Readability metrics
    readability_score: Optional[float] = None             # Flesch Reading Ease (0..100 approx)
    readability_level: Optional[str] = None               # "Easy" / "Medium" / "Hard"
    readability_comment: Optional[str] = None


class AnalyzeResponse(BaseModel):
    uri: str
    result: AnalyzeResult
    created_at: datetime = datetime.now()

class LimitResponse(BaseModel):
    limit: int
    usage: int
    last_reset: str
