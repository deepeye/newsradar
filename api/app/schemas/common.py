"""Common schema fields and base configuration"""
from pydantic import BaseModel, Field, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """Base model with camelCase serialization"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_alias_generator=to_camel,
    )


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(CamelModel):
    total: int
    page: int
    page_size: int