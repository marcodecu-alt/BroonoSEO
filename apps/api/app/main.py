from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .supabase_client import supabase

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
    resp = (
        supabase.table("articles")
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )
    return resp.data


@app.get("/articles/{article_id}")
def get_article(article_id: str):
    article_resp = (
        supabase.table("articles").select("*").eq("id", article_id).execute()
    )
    if not article_resp.data:
        raise HTTPException(status_code=404, detail="article not found")
    article = article_resp.data[0]

    versions_resp = (
        supabase.table("article_versions")
        .select("*")
        .eq("article_id", article_id)
        .order("version_number", desc=True)
        .execute()
    )
    versions = versions_resp.data
    latest_version = versions[0] if versions else None

    review_notes_resp = (
        supabase.table("review_notes")
        .select("*")
        .eq("article_id", article_id)
        .order("created_at", desc=True)
        .execute()
    )

    comments_resp = (
        supabase.table("comments")
        .select("*")
        .eq("article_id", article_id)
        .order("created_at")
        .execute()
    )

    return {
        "article": article,
        "latest_version": latest_version,
        "versions": versions,
        "review_notes": review_notes_resp.data,
        "comments": comments_resp.data,
    }


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
