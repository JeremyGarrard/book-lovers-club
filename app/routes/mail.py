import os
import hashlib

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY", "")
MAILCHIMP_LIST_ID = os.getenv("MAILCHIMP_LIST_ID", "")
MAILCHIMP_SERVER_PREFIX = os.getenv("MAILCHIMP_SERVER_PREFIX", "us1")


@router.post("/signup")
async def mailchimp_signup(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return JSONResponse({"ok": False, "message": "Please enter a valid email address."}, status_code=400)

    if not MAILCHIMP_API_KEY or not MAILCHIMP_LIST_ID:
        # Gracefully succeed without a key (dev mode)
        return JSONResponse({"ok": True, "message": "You're on the list! 📚"})

    url = (
        f"https://{MAILCHIMP_SERVER_PREFIX}.api.mailchimp.com/3.0"
        f"/lists/{MAILCHIMP_LIST_ID}/members"
    )
    subscriber_hash = hashlib.md5(email.encode()).hexdigest()
    put_url = (
        f"https://{MAILCHIMP_SERVER_PREFIX}.api.mailchimp.com/3.0"
        f"/lists/{MAILCHIMP_LIST_ID}/members/{subscriber_hash}"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.put(
            put_url,
            json={"email_address": email, "status_if_new": "subscribed"},
            auth=("anystring", MAILCHIMP_API_KEY),
            timeout=10.0,
        )

    if resp.status_code in (200, 201):
        return JSONResponse({"ok": True, "message": "You're on the list! 📚"})

    detail = resp.json().get("detail", "Something went wrong.")
    return JSONResponse({"ok": False, "message": detail}, status_code=400)
