"""Request bodies. Responses are plain dicts built by the services."""

from pydantic import BaseModel, Field


class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class UserJobIn(BaseModel):
    starred: bool | None = None
    hidden: bool | None = None


class Estimates(BaseModel):
    est_labor: float = Field(ge=0)
    est_material: float = Field(ge=0)
    est_sub: float = Field(ge=0)
    est_misc: float = Field(ge=0)
    contract: float = Field(ge=0)
    pct_complete: float | None = Field(default=None, ge=0, le=100)


class JobIn(Estimates):
    job_number: str = Field(min_length=1, max_length=30)
    qb_list_id: str
    created_by: str | None = None


class NoteIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    author: str | None = None
