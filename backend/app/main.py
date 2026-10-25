from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .fetcher import fetch_page
from .pipeline import analyze_page
from .chatbot import answer_question

app = FastAPI(title="CiteVerity API", version="0.5.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AnalyzeRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    url: str
    question: str
    history: list = []


PAGE_CACHE = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        page = fetch_page(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Couldn't load that page: " + str(e))

    result = analyze_page(page)

    PAGE_CACHE[page.url] = {"text": page.text, "report": result}
    PAGE_CACHE[req.url] = PAGE_CACHE[page.url]
    return result


@app.post("/chat")
def chat(req: ChatRequest):
    cached = PAGE_CACHE.get(req.url)
    if cached is None:
        try:
            page = fetch_page(req.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Couldn't load that page: " + str(e))
        cached = {"text": page.text, "report": None}
        PAGE_CACHE[req.url] = cached

    answer = answer_question(cached["text"], req.question, req.history, cached["report"])
    return {"answer": answer}