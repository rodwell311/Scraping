"""FastAPI wrapper. uvicorn app.main:app --reload"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from src import mode_direct, mode_selector

app = FastAPI(title="AI-Scraper", version="0.1.0")


class ExtractRequest(BaseModel):
    url: HttpUrl
    prompt: str = Field(min_length=1)
    schema_: dict | None = Field(default=None, alias="schema")
    render: bool = False
    model: str | None = None
    max_chars: int = Field(default=40000, ge=500, le=200000)


class GenSelectorRequest(BaseModel):
    url: HttpUrl
    fields: list[str] = Field(min_length=1)
    save_as: str | None = None
    render: bool = False
    model: str | None = None


class ScrapeRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1, max_length=200)
    config: dict | None = None
    config_name: str | None = None
    render: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/extract")
def api_extract(req: ExtractRequest) -> dict:
    try:
        return mode_direct.extract(
            str(req.url), req.prompt, schema=req.schema_,
            render=req.render, max_chars=req.max_chars, model=req.model,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/generate-selector")
def api_generate_selector(req: GenSelectorRequest) -> dict:
    try:
        config = mode_selector.generate_config(
            str(req.url), req.fields, render=req.render, model=req.model
        )
        saved = str(mode_selector.save_config(req.save_as, config)) if req.save_as else None
        return {"config": config, "saved": saved}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/scrape")
def api_scrape(req: ScrapeRequest) -> dict:
    if not req.config and not req.config_name:
        raise HTTPException(status_code=400, detail="config or config_name required")
    try:
        config = req.config or mode_selector.load_config(req.config_name)
        return {"results": mode_selector.scrape(
            [str(u) for u in req.urls], config, render=req.render
        )}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="config not found") from None
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
