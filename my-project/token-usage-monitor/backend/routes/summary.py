"""GET /api/summary?start=YYYY-MM-DD&end=YYYY-MM-DD"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from db import query_summary

router = APIRouter()


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


class DateRange(BaseModel):
    start: Optional[str]
    end: Optional[str]


class SummaryResponse(BaseModel):
    date_range: DateRange
    total: TokenTotals
    rows: list[SummaryRow]


@router.get("/api/summary", response_model=SummaryResponse)
async def get_summary(
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> SummaryResponse:
    rows_raw = query_summary(start, end)

    rows = [
        SummaryRow(
            category=r.get("category", "main_session"),
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
