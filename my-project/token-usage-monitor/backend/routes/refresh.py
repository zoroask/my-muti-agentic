"""POST /api/refresh — re-scan .jsonl files and update SQLite."""
from fastapi import APIRouter
from pydantic import BaseModel

from scanner import TranscriptScanner

router = APIRouter()

_scanner = TranscriptScanner()


class RefreshError(BaseModel):
    file: str
    error: str


class RefreshResponse(BaseModel):
    status: str
    sessions_scanned: int
    errors: list[RefreshError]


@router.post("/api/refresh", response_model=RefreshResponse)
async def refresh() -> RefreshResponse:
    result = _scanner.scan_all()
    return RefreshResponse(
        status=result.get("status", "ok"),
        sessions_scanned=result.get("sessions_scanned", 0),
        errors=[
            RefreshError(
                file=e.get("file", "unknown"),
                error=e.get("error", "unknown error"),
            )
            for e in result.get("errors", [])
        ],
    )
