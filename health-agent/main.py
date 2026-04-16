#!/usr/bin/env python3
"""
Health Content AI Agent — CLI Entry Point

Usage:
  python main.py setup          Initialize the database
  python main.py run            Run the content pipeline once (now)
  python main.py dashboard      Open the review dashboard (localhost:5000)
  python main.py schedule       Start the scheduler (Mon/Wed/Fri automation)
  python main.py canva-auth     Set up Canva API (one-time OAuth flow)
  python main.py list-templates List your Canva templates (find template IDs)
  python main.py refresh-token  Refresh your Instagram access token
  python main.py verify         Verify all credentials are working
"""

import sys
import logging
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

import click
from utils.helpers import configure_logging


@click.group()
def cli():
    """Health Content AI Agent — Instagram automation tool."""
    pass


@cli.command()
def setup():
    """Initialize the database and output directories."""
    configure_logging()
    from database.db import init_db
    import config

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    click.echo("Setup complete.")
    click.echo(f"Database: {config.DATABASE_URL}")
    click.echo(f"Images:   {config.OUTPUT_DIR.resolve()}")
    click.echo("")
    click.echo("Next step: Copy .env.example to .env and fill in your credentials.")


@cli.command()
def run():
    """Run the content pipeline once — scrape, generate, design."""
    configure_logging()
    click.echo("Running content pipeline…")
    from scheduler import run_full_pipeline
    run_full_pipeline()
    click.echo("")
    click.echo("Done. Open the dashboard to review your posts:")
    click.echo("  python main.py dashboard")


@cli.command()
@click.option("--port", default=5000, help="Port to run the dashboard on")
@click.option("--host", default="127.0.0.1", help="Host address")
def dashboard(port, host):
    """Start the review dashboard in your browser."""
    configure_logging(logging.WARNING)
    click.echo(f"Dashboard running at http://{host}:{port}")
    click.echo("Press Ctrl+C to stop.")
    from dashboard.app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=False)


@cli.command()
def schedule():
    """Start the 3x/week automatic scheduler (runs forever)."""
    configure_logging()
    import config
    click.echo(f"Starting scheduler: {config.SCHEDULE_DAYS} at {config.SCHEDULE_TIME}")
    click.echo("Press Ctrl+C to stop.")
    from scheduler import start_scheduler
    start_scheduler()


@cli.command("canva-auth")
def canva_auth():
    """Run the one-time Canva OAuth flow to get API tokens."""
    import config
    if not config.CANVA_CLIENT_ID or not config.CANVA_CLIENT_SECRET:
        click.echo("ERROR: Set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET in your .env first.")
        click.echo("Get them from: https://www.canva.com/developers/")
        sys.exit(1)

    from designer.canva_client import CanvaClient
    client = CanvaClient()
    client.run_oauth_flow()
    click.echo("")
    click.echo("Canva is ready. Your tokens are saved to .env")
    click.echo("Next: run 'python main.py list-templates' to find your template IDs.")


@cli.command("list-templates")
def list_templates():
    """List your Canva designs so you can find template IDs."""
    from designer.canva_client import CanvaClient
    client = CanvaClient()
    designs = client.list_designs()

    if not designs:
        click.echo("No designs found. Create templates in Canva first.")
        return

    click.echo(f"\nFound {len(designs)} design(s):\n")
    for d in designs:
        click.echo(f"  ID: {d.get('id')}")
        click.echo(f"  Name: {d.get('title', '(no title)')}")
        click.echo(f"  URL:  {d.get('urls', {}).get('view_url', '')}")
        click.echo()

    click.echo("Copy the ID of your templates to .env:")
    click.echo("  CANVA_SINGLE_POST_TEMPLATE_ID=<id>")
    click.echo("  CANVA_CAROUSEL_TEMPLATE_ID=<id>")


@cli.command("refresh-token")
def refresh_token():
    """Refresh your Instagram long-lived access token (do this every ~50 days)."""
    import config
    if not config.INSTAGRAM_ACCESS_TOKEN:
        click.echo("ERROR: INSTAGRAM_ACCESS_TOKEN not set in .env")
        sys.exit(1)

    from publisher.instagram import refresh_long_lived_token
    new_token = refresh_long_lived_token()

    # Update .env
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        content = env_path.read_text()
        if "INSTAGRAM_ACCESS_TOKEN=" in content:
            lines = content.splitlines()
            content = "\n".join(
                f"INSTAGRAM_ACCESS_TOKEN={new_token}"
                if line.startswith("INSTAGRAM_ACCESS_TOKEN=")
                else line
                for line in lines
            )
            env_path.write_text(content)

    click.echo("Instagram token refreshed and saved to .env")


@cli.command()
def verify():
    """Verify all API credentials are working."""
    configure_logging(logging.WARNING)
    import config
    errors = []
    warnings = []

    click.echo("Checking credentials…\n")

    # Claude
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}],
            )
            click.echo("  Claude API       OK")
        except Exception as e:
            errors.append(f"Claude API: {e}")
            click.echo(f"  Claude API       FAIL — {e}")
    else:
        errors.append("ANTHROPIC_API_KEY not set")
        click.echo("  Claude API       MISSING")

    # Canva
    if config.CANVA_ACCESS_TOKEN:
        try:
            from designer.canva_client import CanvaClient
            CanvaClient().list_designs()
            click.echo("  Canva API        OK")
        except Exception as e:
            warnings.append(f"Canva API: {e}")
            click.echo(f"  Canva API        WARN — {e}")
    else:
        warnings.append("Canva not yet authorised — run: python main.py canva-auth")
        click.echo("  Canva API        NOT CONFIGURED")

    # Instagram
    if config.INSTAGRAM_USER_ID and config.INSTAGRAM_ACCESS_TOKEN:
        try:
            from publisher.instagram import get_account_info
            info = get_account_info()
            click.echo(f"  Instagram API    OK — @{info.get('username', '?')} ({info.get('account_type', '?')})")
        except Exception as e:
            errors.append(f"Instagram API: {e}")
            click.echo(f"  Instagram API    FAIL — {e}")
    else:
        warnings.append("Instagram credentials not set")
        click.echo("  Instagram API    NOT CONFIGURED")

    # PubMed
    if config.PUBMED_API_KEY:
        click.echo("  PubMed API       OK (key set)")
    else:
        click.echo("  PubMed API       OK (no key — 3 req/s limit applies)")

    click.echo()
    if errors:
        click.echo(f"  {len(errors)} error(s) — fix these before running the pipeline")
    elif warnings:
        click.echo(f"  Ready (with {len(warnings)} warning(s) — see above)")
    else:
        click.echo("  All systems go. Run: python main.py run")


@cli.command("generate-images")
def generate_images():
    """Generate images for any posts in the queue that don't have them yet."""
    configure_logging()
    from database.db import get_session, init_db
    from database.models import Post
    from designer.templates import create_post_images
    from processor.generator import GeneratedPost
    import json

    init_db()

    with get_session() as db:
        posts = db.query(Post).filter(
            Post.status.in_(["draft", "approved"]),
        ).all()

        no_images = [p for p in posts if not p.get_image_paths()]

    if not no_images:
        click.echo("All posts already have images.")
        return

    click.echo(f"Generating images for {len(no_images)} post(s)…")

    for p in no_images:
        slides = p.get_slide_texts()
        post_content = GeneratedPost(
            format=p.format,
            hook=p.hook or "",
            caption=p.caption,
            hashtags=p.get_hashtags(),
            slides=slides,
        )
        try:
            paths = create_post_images(post_content, p.id)
            with get_session() as db:
                post = db.query(Post).filter_by(id=p.id).first()
                if post:
                    post.set_image_paths(paths)
            click.echo(f"  Post {p.id}: {len(paths)} image(s) created")
        except Exception as exc:
            click.echo(f"  Post {p.id}: FAILED — {exc}")

    click.echo("Done. Refresh your dashboard to see the images.")


if __name__ == "__main__":
    cli()
