from pydantic import BaseModel


class RegionIconOut(BaseModel):
    name: str
    format: str
    icon_url: str
