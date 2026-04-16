"""
Flask review dashboard.

Routes:
  GET/POST /login              → Password login
  GET      /logout             → Log out
  GET      /canva/auth         → Start Canva OAuth (cloud-friendly)
  GET      /canva/callback     → Canva OAuth redirect handler
  GET      /                   → Queue of draft/approved posts
  GET      /post/<id>          → Single post detail + edit form
  POST     /post/<id>          → Save edits (caption, hashtags)
  POST     /post/<id>/approve  → Mark as approved
  POST     /post/<id>/reject   → Mark as rejected
  POST     /post/<id>/publish  → Publish immediately to Instagram
  GET      /history            → All posted content
  GET      /image/<id>/<idx>   → Serve post image
"""

import hashlib
import base64
import secrets
import logging
import sys
import urllib.parse
from datetime import datetime
from functools import wraps
from pathlib import Path

import requests
from flask import (
    Flask, flash, redirect, render_template,
    request, send_file, session, url_for,
)

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


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ─── Auth routes ─────────────────────────────────────────────────────────────


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("queue"))

    if request.method == "POST":
        entered = request.form.get("password", "")
        if config.DASHBOARD_PASSWORD and entered == config.DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("queue"))
        flash("Wrong password. Try again.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Logged out.", "info")
    return redirect(url_for("login"))


# ─── Canva OAuth (cloud-friendly — no localhost server needed) ───────────────


@app.route("/canva/auth")
@login_required
def canva_auth_start():
    """Generate PKCE + redirect user to Canva authorisation page."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)

    session["canva_code_verifier"] = code_verifier
    session["canva_state"] = state

    params = {
        "client_id": config.CANVA_CLIENT_ID,
        "redirect_uri": config.CANVA_REDIRECT_URI,
        "response_type": "code",
        "scope": "design:content:write design:content:read asset:read asset:write",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{config.CANVA_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@app.route("/canva/callback")
@login_required
def canva_auth_callback():
    """Handle Canva OAuth redirect, exchange code for tokens, save to .env."""
    error = request.args.get("error")
    if error:
        flash(f"Canva authorisation failed: {error}", "error")
        return redirect(url_for("queue"))

    code = request.args.get("code")
    returned_state = request.args.get("state")

    if returned_state != session.get("canva_state"):
        flash("OAuth state mismatch — please try again.", "error")
        return redirect(url_for("queue"))

    code_verifier = session.pop("canva_code_verifier", "")

    try:
        resp = requests.post(
            config.CANVA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.CANVA_REDIRECT_URI,
                "client_id": config.CANVA_CLIENT_ID,
                "client_secret": config.CANVA_CLIENT_SECRET,
                "code_verifier": code_verifier,
            },
            timeout=15,
        )
        resp.raise_for_status()
        tokens = resp.json()
    except Exception as exc:
        flash(f"Failed to exchange Canva token: {exc}", "error")
        return redirect(url_for("queue"))

    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    _save_canva_tokens(access_token, refresh_token)
    flash("Canva connected successfully!", "success")
    return redirect(url_for("queue"))


def _save_canva_tokens(access_token: str, refresh_token: str) -> None:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        env_path.touch()

    content = env_path.read_text()
    for key, value in [("CANVA_ACCESS_TOKEN", access_token), ("CANVA_REFRESH_TOKEN", refresh_token)]:
        if f"{key}=" in content:
            lines = content.splitlines()
            content = "\n".join(
                f"{key}={value}" if line.startswith(f"{key}=") else line
                for line in lines
            )
        else:
            content += f"\n{key}={value}"
    env_path.write_text(content)


# ─── Main routes ─────────────────────────────────────────────────────────────


@app.route("/")
@login_required
def queue():
    with get_session() as db:
        posts = (
            db.query(Post)
            .filter(Post.status.in_(["draft", "approved"]))
            .order_by(Post.created_at.desc())
            .all()
        )
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

    canva_configured = bool(config.CANVA_ACCESS_TOKEN and config.CANVA_CLIENT_ID)
    return render_template("queue.html", posts=post_data, canva_configured=canva_configured)


@app.route("/post/<int:post_id>", methods=["GET"])
@login_required
def post_detail(post_id: int):
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
@login_required
def post_save(post_id: int):
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
@login_required
def post_approve(post_id: int):
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if post and post.status == "draft":
            post.status = "approved"
            flash("Post approved — ready to publish.", "success")
        else:
            flash("Post could not be approved.", "error")
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/post/<int:post_id>/reject", methods=["POST"])
@login_required
def post_reject(post_id: int):
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if post:
            post.status = "rejected"
            flash("Post rejected.", "info")
    return redirect(url_for("queue"))


@app.route("/post/<int:post_id>/publish", methods=["POST"])
@login_required
def post_publish(post_id: int):
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
            flash("No images found. Canva design may not have run yet.", "error")
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
@login_required
def history():
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
@login_required
def serve_image(post_id: int, slide_index: int):
    with get_session() as db:
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            return "Not found", 404
        paths = post.get_image_paths()

    if slide_index >= len(paths):
        return "Image not found", 404

    path = Path(paths[slide_index])

    # Resolve relative paths against the project root
    if not path.is_absolute():
        project_root = Path(__file__).parent.parent
        path = project_root / path

    if not path.exists():
        return f"Image file missing: {path}", 404

    return send_file(path, mimetype="image/png")


def create_app() -> Flask:
    init_db()
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
