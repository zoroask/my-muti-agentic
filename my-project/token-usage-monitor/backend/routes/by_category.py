"""
GET /api/by-agent
GET /api/by-skill
GET /api/by-command
Each returns the same shape as /api/summary, rows filtered to the named attribution category.
"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from db import query_by_category

router = APIRouter()


class DateRange(BaseModel):
    start: Optional[str]
    end: Optional[str]


class TokenTotals(BaseModel):
    input: int
    output: int
    cache_read: int
    cache_write: int


class SummaryRow(BaseModel):
    category: str
    name: str
    input: int
    output: int
    cache_read: int
    cache_write: int


class SummaryResponse(BaseModel):
    date_range: DateRange
    total: TokenTotals
    rows: list[SummaryRow]


def _build_response(category: str, start: Optional[str], end: Optional[str]) -> SummaryResponse:
    rows_raw = query_by_category(category, start, end)
    rows = [
        SummaryRow(
            category=r.get("category", category),
            name=r.get("name", "unknown"),
            input=r.get("input", 0),
            output=r.get("output", 0),
            cache_read=r.get("cache_read", 0),
            cache_write=r.get("cache_write", 0),
        )
        for r in rows_raw
    ]
    total = TokenTotals(
        input=sum(r.input for r in rows),
        output=sum(r.output for r in rows),
        cache_read=sum(r.cache_read for r in rows),
        cache_write=sum(r.cache_write for r in rows),
    )
    return SummaryResponse(
        date_range=DateRange(start=start, end=end),
        total=total,
        rows=rows,
    )


@router.get("/api/by-agent", response_model=SummaryResponse)
async def by_agent(
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> SummaryResponse:
    return _build_response("agent", start, end)


@router.get("/api/by-skill", response_model=SummaryResponse)
async def by_skill(
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> SummaryResponse:
    return _build_response("skill", start, end)


@router.get("/api/by-command", response_model=SummaryResponse)
async def by_command(
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> SummaryResponse:
    return _build_response("command", start, end)
