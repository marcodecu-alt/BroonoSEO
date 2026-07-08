from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Broono SEO Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


class StartArticleRequest(BaseModel):
    topic_seed: str | None = None


class CommentRequest(BaseModel):
    comment_text: str
    user_id: str


@app.post("/articles/start")
def start_article(body: StartArticleRequest):
    # TODO: kick off pipeline_graph.invoke(...) as a background run, persist article row
    raise HTTPException(status_code=501, detail="not implemented")


@app.get("/articles")
def list_articles():
    # TODO: read from Supabase articles table
    return []


@app.get("/articles/{article_id}")
def get_article(article_id: str):
    # TODO: read article + latest draft + review notes + comments from Supabase
    raise HTTPException(status_code=501, detail="not implemented")


@app.post("/articles/{article_id}/approve")
def approve_article(article_id: str):
    # TODO: set status=approved, trigger export step
    raise HTTPException(status_code=501, detail="not implemented")


@app.post("/articles/{article_id}/comment")
def comment_on_article(article_id: str, body: CommentRequest):
    # TODO: persist comment, resume graph from draft_node with comment as revision context
    raise HTTPException(status_code=501, detail="not implemented")


@app.get("/articles/{article_id}/export")
def export_article(article_id: str):
    # TODO: return formatted markdown for the approved version
    raise HTTPException(status_code=501, detail="not implemented")
