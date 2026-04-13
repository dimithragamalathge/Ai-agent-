"""
Flask review dashboard — runs on localhost:5000.

Routes:
  GET  /              → Queue of draft/approved posts
  GET  /post/<id>     → Single post detail + edit form
  POST /post/<id>     → Save edits (caption, hashtags, format)
  POST /post/<id>/approve   → Mark as approved
  POST /post/<id>/reject    → Mark as rejected
  POST /post/<id>/publish   → Publish immediately to Instagram
  GET  /history       → All posted content
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from database.db import get_session, init_db
from database.models import Post, Article

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.FLASK_SECRET_KEY


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _format_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d %b %Y, %H:%M")


app.jinja_env.filters["dt"] = _format_dt


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.route("/")
def queue():
    """Show all posts that need review (draft or approved)."""
    with get_session() as db:
        posts = (
            db.query(Post)
            .filter(Post.status.in_(["draft", "approved"]))
            .order_by(Post.created_at.desc())
            .all()
        )
        # Eagerly load article titles
        post_data = []
        for p in posts:
            article_title = p.article.title if p.article else "—"
            post_data.append({
                "id": p.id,
                "format": p.format,
                "hook": p.hook or p.caption[:80],
                "status": p.status,
                "created_at": p.created_at,
                "article_title": article_title,
                "image_paths": p.get_image_paths(),
            })

    return render_template("queue.html", posts=post_data)


@app.route("/post/<int:post_id>", methods=["GET"])
def post_detail(post_id: int):
    """Show a single post with full preview and edit form."""
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            flash("Post not found.", "error")
            return redirect(url_for("queue"))

        article_title = post.article.title if post.article else "—"
        article_url = post.article.url if post.article else "#"

        data = {
            "id": post.id,
            "format": post.format,
            "hook": post.hook or "",
            "caption": post.caption,
            "hashtags": " ".join(post.get_hashtags()),
            "slides": post.get_slide_texts(),
            "status": post.status,
            "created_at": post.created_at,
            "posted_at": post.posted_at,
            "instagram_media_id": post.instagram_media_id,
            "canva_design_id": post.canva_design_id,
            "image_paths": post.get_image_paths(),
            "article_title": article_title,
            "article_url": article_url,
        }

    return render_template("post_detail.html", post=data)


@app.route("/post/<int:post_id>", methods=["POST"])
def post_save(post_id: int):
    """Save edited caption, hashtags, and format."""
    caption = request.form.get("caption", "").strip()
    hashtags_raw = request.form.get("hashtags", "").strip()
    hashtags = [t.strip() for t in hashtags_raw.replace(",", " ").split() if t.strip()]

    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            flash("Post not found.", "error")
            return redirect(url_for("queue"))

        post.caption = caption
        post.set_hashtags(hashtags)

    flash("Post saved successfully.", "success")
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/post/<int:post_id>/approve", methods=["POST"])
def post_approve(post_id: int):
    """Mark a post as approved (ready to publish)."""
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if post and post.status == "draft":
            post.status = "approved"
            flash("Post approved — ready to publish.", "success")
        else:
            flash("Post could not be approved.", "error")

    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/post/<int:post_id>/reject", methods=["POST"])
def post_reject(post_id: int):
    """Mark a post as rejected."""
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if post:
            post.status = "rejected"
            flash("Post rejected.", "info")

    return redirect(url_for("queue"))


@app.route("/post/<int:post_id>/publish", methods=["POST"])
def post_publish(post_id: int):
    """Publish an approved post immediately to Instagram."""
    from publisher.instagram import publish_post

    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            flash("Post not found.", "error")
            return redirect(url_for("queue"))

        if post.status not in ("draft", "approved"):
            flash("Only draft or approved posts can be published.", "error")
            return redirect(url_for("post_detail", post_id=post_id))

        image_paths = post.get_image_paths()
        if not image_paths:
            flash(
                "No images found for this post. "
                "Canva design may not have been generated yet.",
                "error",
            )
            return redirect(url_for("post_detail", post_id=post_id))

        try:
            media_id = publish_post(
                image_paths=image_paths,
                caption=post.caption,
                hashtags=post.get_hashtags(),
                post_format=post.format,
            )
            post.status = "posted"
            post.posted_at = datetime.utcnow()
            post.instagram_media_id = media_id
            flash(f"Posted to Instagram! Media ID: {media_id}", "success")
        except Exception as exc:
            post.status = "failed"
            logger.error("Publish failed for post %d: %s", post_id, exc)
            flash(f"Publish failed: {exc}", "error")

    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/history")
def history():
    """Show all posted and failed posts."""
    with get_session() as db:
        posts = (
            db.query(Post)
            .filter(Post.status.in_(["posted", "failed", "rejected"]))
            .order_by(Post.posted_at.desc().nullslast(), Post.created_at.desc())
            .all()
        )
        post_data = [
            {
                "id": p.id,
                "format": p.format,
                "hook": p.hook or p.caption[:80],
                "status": p.status,
                "created_at": p.created_at,
                "posted_at": p.posted_at,
                "instagram_media_id": p.instagram_media_id,
                "article_title": p.article.title if p.article else "—",
            }
            for p in posts
        ]

    return render_template("history.html", posts=post_data)


@app.route("/image/<int:post_id>/<int:slide_index>")
def serve_image(post_id: int, slide_index: int):
    """Serve a local post image so the dashboard can display it."""
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            return "Not found", 404
        paths = post.get_image_paths()

    if slide_index >= len(paths):
        return "Image not found", 404

    path = Path(paths[slide_index])
    if not path.exists():
        return "Image file missing from disk", 404

    return send_file(path, mimetype="image/png")


def create_app() -> Flask:
    init_db()
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
