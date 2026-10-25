import os
import re
import httpx

OLLAMA_URL = "https://ollama.com" 
API_KEY = os.getenv("OLLAMA_API_KEY")
MODEL = "gemma4:31b"

MAX_HISTORY = 6 

STOPWORDS = set("""a an the and or but if of to in on at for with about is are was were be been
it this that these those what who why how when where which does do did can could would should
as by from not no yes you your i me my we our they them their he she his her its so than then
there here have has had will just tell say says said article page""".split())

def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in STOPWORDS and len(w) > 1]

def split_into_chunks(text, size=150, overlap=30):
    words = text.split()
    chunks, step = [], size - overlap
    for start in range(0, len(words), step):
        piece = words[start:start + size]
        if piece:
            chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks

def pick_chunks(text, question, k=4):
    chunks = split_into_chunks(text)
    if not chunks:
        return []

    q_words = set(tokenize(question))
    scored = []
    for i, chunk in enumerate(chunks):
        words = tokenize(chunk)
        hits = sum(1 for w in words if w in q_words)
        scored.append((hits / ((len(words) ** 0.5) + 1), i, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[:k]

    if best[0][0] == 0:
        return chunks[:k]

    best.sort(key=lambda x: x[1])
    return [c for _, _, c in best]

def report_to_text(report):
    if not report:
        return ""
    lines = ["Trust score: " + str(report.get("score")) + "% (" + str(report.get("tier")) + ")."]
    for p in report.get("penalties", []):
        lines.append("- lost " + str(p.get("points")) + " points: " + str(p.get("reason")))
    return "\n".join(lines)

def build_messages(excerpts, question, history=None, report_text=""):
    system = (
        "You are the CiteVerity assistant. You help people understand a web page.\n"
        "Answer ONLY using the page excerpts and the trust report below.\n"
        "If the answer is not in them, say you can't find that on the page. Never guess or invent facts.\n"
        "Keep answers short and in plain language.\n\n"
        "PAGE EXCERPTS:\n" + "\n---\n".join(excerpts)
    )
    if report_text:
        system += "\n\nTRUST REPORT:\n" + report_text

    messages = [{"role": "system", "content": system}]

    good = [m for m in (history or [])
            if m.get("role") in ("user", "assistant") and m.get("content")]
    for m in good[-MAX_HISTORY:]:
        messages.append({"role": m["role"], "content": m["content"]})

    messages.append({"role": "user", "content": question})
    return messages

def ask_ollama(messages):
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Sending the request to the Ollama Cloud API
        r = httpx.post(OLLAMA_URL + "/api/chat",
                       headers=headers,
                       json={"model": MODEL, "messages": messages, "stream": False},
                       timeout=120)
    except Exception as e:
        return f"I can't reach the AI service right now. (Error: {str(e)})"

    if r.status_code == 401:
        return "Invalid API Key. Please check your Ollama key."
    if r.status_code == 404:
        return "The AI model could not be found on the server. Check the model name."
    if r.status_code != 200:
        return f"The AI service returned an error (Status {r.status_code})."
    
    try:
        return r.json()["message"]["content"].strip()
    except Exception:
        return "The AI sent back an unexpected response format."

def answer_question(page_text, question, history=None, report=None):
    excerpts = pick_chunks(page_text, question)
    if not excerpts:
        return "I couldn't read any text from that page."
    messages = build_messages(excerpts, question, history, report_to_text(report))
    return ask_ollama(messages)