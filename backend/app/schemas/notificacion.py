from typing import Literal

from pydantic import BaseModel, Field


class DispositivoPushIn(BaseModel):
    token: str = Field(..., min_length=20, max_length=512)
    plataforma: Literal["android"] = "android"


class DispositivoPushOut(BaseModel):
    registrado: bool
