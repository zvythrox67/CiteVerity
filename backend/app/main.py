from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.scoring import calculate_score
from app.detectives import ALL_DETECTIVES

app = FastAPI(title="CiteVerity")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UrlRequest(BaseModel):
    url: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: UrlRequest):
    page = {"url": req.url, "html": "", "text": ""}

    penalties = []
    for detective in ALL_DETECTIVES:
        penalties += detective(page)

    result = calculate_score(penalties)
    result["url"] = req.url
    return result