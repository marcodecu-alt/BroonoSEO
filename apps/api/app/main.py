import os

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .pipeline_runner import resume_pipeline_with_comment, run_pipeline_and_persist
from .supabase_client import supabase

app = FastAPI(title="Broono SEO Pipeline API")

# ALLOWED_ORIGINS is a comma-separated list, e.g. "https://broono-seo.vercel.app".
# Defaults to local dev only.
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
def start_article(body: StartArticleRequest, background_tasks: BackgroundTasks):
    resp = (
        supabase.table("articles")
        .insert({"status": "researching", "brief_json": {}})
        .execute()
    )
    article = resp.data[0]

    background_tasks.add_task(run_pipeline_and_persist, article["id"], body.topic_seed)

    return article


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
    resp = (
        supabase.table("articles")
        .update({"status": "approved"})
        .eq("id", article_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="article not found")
    return resp.data[0]


@app.post("/articles/{article_id}/comment")
def comment_on_article(
    article_id: str, body: CommentRequest, background_tasks: BackgroundTasks
):
    article_resp = (
        supabase.table("articles").select("id").eq("id", article_id).execute()
    )
    if not article_resp.data:
        raise HTTPException(status_code=404, detail="article not found")

    version_resp = (
        supabase.table("article_versions")
        .select("id")
        .eq("article_id", article_id)
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )
    if not version_resp.data:
        raise HTTPException(status_code=400, detail="article has no draft yet")
    version_id = version_resp.data[0]["id"]

    supabase.table("comments").insert(
        {
            "article_id": article_id,
            "version_id": version_id,
            "user_id": body.user_id,
            "comment_text": body.comment_text,
        }
    ).execute()

    supabase.table("articles").update({"status": "drafting"}).eq(
        "id", article_id
    ).execute()

    background_tasks.add_task(
        resume_pipeline_with_comment, article_id, body.comment_text
    )

    return {"status": "drafting"}


@app.get("/articles/{article_id}/export")
def export_article(article_id: str):
    article_resp = (
        supabase.table("articles").select("*").eq("id", article_id).execute()
    )
    if not article_resp.data:
        raise HTTPException(status_code=404, detail="article not found")
    article = article_resp.data[0]

    if article["status"] != "approved":
        raise HTTPException(status_code=400, detail="article is not approved yet")

    version_resp = (
        supabase.table("article_versions")
        .select("content")
        .eq("article_id", article_id)
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )
    if not version_resp.data:
        raise HTTPException(status_code=404, detail="no version found")

    return PlainTextResponse(version_resp.data[0]["content"], media_type="text/markdown")
