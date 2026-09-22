from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class SearchTermBase(BaseModel):
    term: str = Field(..., max_length=255)
    category: str = "general"
    active: bool = True

    @field_validator("term")
    @classmethod
    def strip_and_validate_term(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Search term must not be empty")
        if len(v) < 2:
            raise ValueError("Search term must be at least 2 characters")
        return v

    @field_validator("category")
    @classmethod
    def strip_and_validate_category(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Category must not be empty")
        return v


class SearchTermCreate(SearchTermBase):
    pass


class SearchTermUpdate(BaseModel):
    term: str | None = Field(None, max_length=255)
    category: str | None = None
    active: bool | None = None

    @field_validator("term")
    @classmethod
    def strip_and_validate_term(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Search term must not be empty")
        if len(v) < 2:
            raise ValueError("Search term must be at least 2 characters")
        return v

    @field_validator("category")
    @classmethod
    def strip_and_validate_category(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Category must not be empty")
        return v


class SearchTermResponse(SearchTermBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchTermWithCoverage(SearchTermBase):
    """A search term plus how much stored trend history actually backs it.

    The UI uses ``has_trends`` to avoid charting a term that has no rows yet.
    """

    id: int
    created_at: datetime
    trend_row_count: int = 0
    trend_first_date: date | None = None
    trend_last_date: date | None = None
    has_trends: bool = False

    model_config = {"from_attributes": True}
