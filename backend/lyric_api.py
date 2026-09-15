from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from lyric_engine import LyricRequest, build_lyric_draft

router = APIRouter(prefix="/lyrics", tags=["lyrics"])


class LyricBody(BaseModel):
    idea: str = Field(min_length=3, max_length=500)
    mood: str = Field(default="emotional", max_length=50)
    language: str = Field(default="Nepali", max_length=30)
    perspective: str = Field(default="first-person", max_length=30)


@router.post("/draft")
def draft(body: LyricBody):
    try:
        return build_lyric_draft(LyricRequest(**body.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
