"""Digest matching engine and email notification service.

Flow:
  1. After each scrape, match_and_enqueue() pushes matching job→user pairs
     into digest_queue (deduped per user+job).
  2. A nightly task (or manual trigger) calls send_daily_digests() which
     groups unsent entries by user, builds one HTML email per user,
     and sends via Resend API.
"""

import logging
from datetime import datetime, timezone
from collections import defaultdict

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User
from ..models.job import Job
from ..models.subscription import Subscription
from ..models.digest_queue import DigestQueue
from ..models.application import Application

logger = logging.getLogger(__name__)


# ── Matching ──────────────────────────────────────────────────

def match_and_enqueue(db: Session, new_job_ids: list[str]) -> int:
    """Match newly scraped jobs against active subscriptions.

    For each subscription, check if any new job matches its criteria:
      - keywords in job.title or job.description (case-insensitive)
      - cities match (case-insensitive contains)
      - job_types match

    Matched pairs are inserted into digest_queue (skip if user+job already queued).

    Returns: number of new digest_queue entries created.
    """
    if not new_job_ids:
        return 0

    # Fetch new jobs
    jobs = db.execute(
        select(Job).where(Job.id.in_(new_job_ids), Job.is_active == True)
    ).scalars().all()

    # Fetch all enabled subscriptions with their users
    subs_stmt = (
        select(Subscription, User)
        .join(User, Subscription.user_id == User.id)
        .where(Subscription.enabled == True)
    )
    sub_rows = db.execute(subs_stmt).all()

    # Build set of existing (user_id, job_id) to skip duplicates
    existing = set()
    for row in db.execute(
        select(DigestQueue.user_id, DigestQueue.job_id).where(
            DigestQueue.is_sent == False
        )
    ).all():
        existing.add((str(row[0]), str(row[1])))

    enqueued = 0
    for sub, user in sub_rows:
        for job in jobs:
            pair = (str(user.id), str(job.id))
            if pair in existing:
                continue

            if _job_matches_subscription(job, sub):
                entry = DigestQueue(
                    user_id=user.id,
                    job_id=job.id,
                    is_sent=False,
                )
                db.add(entry)
                existing.add(pair)
                enqueued += 1

    db.commit()
    if enqueued:
        logger.info(
            "Digest match: %d new entries from %d jobs × %d subscriptions",
            enqueued, len(jobs), len(sub_rows),
        )
    return enqueued


def _job_matches_subscription(job: Job, sub: Subscription) -> bool:
    """Check if a job matches a single subscription's criteria.

    All non-empty filter groups must match (AND logic within groups).
    Returns False if subscription has no criteria (safety guard).
    """
    has_criteria = False

    # Keyword matching
    if sub.keywords:
        has_criteria = True
        search_text = (
            (job.title or "") + " " + (job.description or "")
        ).lower()
        if not any(kw.lower() in search_text for kw in sub.keywords):
            return False

    # City matching
    if sub.cities:
        has_criteria = True
        job_city = (job.city or "").lower()
        if not any(c.lower() in job_city for c in sub.cities):
            return False

    # Job type matching
    if sub.job_types:
        has_criteria = True
        job_type = (job.job_type or "").lower()
        if not any(t.lower() == job_type for t in sub.job_types):
            return False

    # Safety: if no criteria at all, don't match everything
    return has_criteria


# ── Email sending ─────────────────────────────────────────────

def send_daily_digests(db: Session) -> dict:
    """Aggregate unsent digest entries, build HTML emails, and send via Resend.

    - Groups unsent digest_queue rows by user
    - Builds one HTML email per user summarizing matched jobs
    - Sends via Resend API
    - Marks entries as is_sent=True
    - Updates subscription.last_sent_at

    Returns: {"sent": int, "failed": int, "skipped": int}
    """
    # Fetch unsent entries with job + user info
    stmt = (
        select(DigestQueue, User, Job)
        .join(User, DigestQueue.user_id == User.id)
        .join(Job, DigestQueue.job_id == Job.id)
        .where(DigestQueue.is_sent == False)
    )
    rows = db.execute(stmt).all()

    if not rows:
        return {"sent": 0, "failed": 0, "skipped": 0}

    # Group by user
    user_jobs: dict[str, dict] = defaultdict(lambda: {"user": None, "jobs": [], "entries": []})
    for entry, user, job in rows:
        uid = str(user.id)
        user_jobs[uid]["user"] = user
        user_jobs[uid]["entries"].append(entry)
        user_jobs[uid]["jobs"].append(job)

    sent = 0
    failed = 0
    skipped = 0

    for uid, data in user_jobs.items():
        user = data["user"]
        entries = data["entries"]
        jobs = data["jobs"]

        try:
            html = _build_digest_html(user, jobs)
            success = _send_email_via_resend(
                to_email=user.email,
                subject=f"InternHub — {len(jobs)} 个新岗位匹配 · {datetime.now(timezone.utc).strftime('%m月%d日')}",
                html=html,
            )

            if success:
                # Mark entries as sent
                for entry in entries:
                    entry.is_sent = True
                # Update subscription last_sent_at
                sub_stmt = select(Subscription).where(Subscription.user_id == user.id)
                sub = db.execute(sub_stmt).scalar_one_or_none()
                if sub:
                    sub.last_sent_at = datetime.now(timezone.utc)
                sent += 1
            else:
                failed += 1
                logger.error("Failed to send digest to %s", user.email)

        except Exception:
            failed += 1
            logger.exception("Exception sending digest to %s", user.email)

    db.commit()
    logger.info("Digest send complete: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {"sent": sent, "failed": failed, "skipped": skipped}


def _build_digest_html(user: User, jobs: list[Job]) -> str:
    """Build an HTML digest email for one user."""
    job_items = []
    for job in jobs:
        salary = ""
        if job.salary_min and job.salary_max:
            salary = f"¥{job.salary_min//1000}k-¥{job.salary_max//1000}k/月"
        elif job.salary_min:
            salary = f"¥{job.salary_min//1000}k起/月"

        city = job.city or ""
        source = job.source or ""

        job_items.append(f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #eee">
            <p style="margin:0 0 4px;font-size:14px;font-weight:600;color:#1D1D1F">
              {_escape(job.title)}
            </p>
            <p style="margin:0 0 4px;font-size:13px;color:#86868B">
              🏢 {_escape(job.company)}
              {f" · 📍 {_escape(city)}" if city else ""}
              {f" · 💰 {_escape(salary)}" if salary else ""}
            </p>
            <p style="margin:0;font-size:12px;color:#86868B">
              来源: {_escape(source)} ·
              <a href="{_escape(job.source_url)}" style="color:#0071E3;text-decoration:none">
                查看原文 →
              </a>
            </p>
          </td>
        </tr>
        """)

    nickname = user.nickname or user.email.split("@")[0]

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#F5F5F7;font-family:-apple-system,system-ui,sans-serif">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;padding:24px">
        <tr>
          <td style="padding:32px 24px;text-align:center">
            <h1 style="margin:0 0 8px;font-size:24px;color:#0071E3">🔔 InternHub 岗位速递</h1>
            <p style="margin:0;font-size:14px;color:#86868B">
              你好 {_escape(nickname)}，以下是为你匹配的 {len(jobs)} 个新岗位
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#fff;border-radius:16px;padding:0 8px">
            <table width="100%" cellpadding="0" cellspacing="0">
              {''.join(job_items)}
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:24px;text-align:center">
            <p style="margin:0 0 12px;font-size:12px;color:#86868B">
              此邮件由 InternHub 自动发送 ·
              <a href="#" style="color:#0071E3">管理订阅</a> ·
              <a href="#" style="color:#0071E3">退订</a>
            </p>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def _send_email_via_resend(to_email: str, subject: str, html: str) -> bool:
    """Send an email via the Resend API. Returns True on success."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured — skipping email to %s", to_email)
        return False  # Don't block; just log and skip

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html,
            },
            timeout=30.0,
        )
        if resp.status_code in (200, 201):
            return True
        logger.error("Resend API error %d: %s", resp.status_code, resp.text)
        return False
    except Exception:
        logger.exception("Resend API request failed")
        return False


def _escape(text: str) -> str:
    """Basic HTML escape."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
