import base64
from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx

from config import settings


GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]


class GoogleOAuthClient:
    token_url = "https://oauth2.googleapis.com/token"
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"

    def is_configured(self) -> bool:
        client_id = settings.google_calendar_client_id or settings.gmail_client_id
        client_secret = settings.google_calendar_client_secret or settings.gmail_client_secret
        return bool(client_id and client_secret)

    def client_id(self) -> str:
        return settings.google_calendar_client_id or settings.gmail_client_id

    def client_secret(self) -> str:
        return settings.google_calendar_client_secret or settings.gmail_client_secret

    def has_refresh_token(self) -> bool:
        return bool(settings.google_refresh_token)

    def get_auth_url(self, redirect_uri: str, state: str | None = None) -> str:
        params = {
            "client_id": self.client_id(),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        if state:
            params["state"] = state
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        if not self.is_configured():
            raise RuntimeError("Google OAuth client ID/secret are not configured.")

        data = {
            "code": code,
            "client_id": self.client_id(),
            "client_secret": self.client_secret(),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()

    async def access_token(self) -> str:
        if not self.has_refresh_token():
            raise RuntimeError("GOOGLE_REFRESH_TOKEN is missing. Complete Google OAuth first.")

        data = {
            "client_id": self.client_id(),
            "client_secret": self.client_secret(),
            "refresh_token": settings.google_refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            payload = response.json()
            return payload["access_token"]

    async def auth_headers(self) -> dict:
        token = await self.access_token()
        return {"Authorization": f"Bearer {token}"}


class GmailClient:
    base_url = "https://gmail.googleapis.com/gmail/v1/users/me"

    def is_configured(self) -> bool:
        return google_oauth.is_configured() and google_oauth.has_refresh_token()

    async def list_unread_emails(self, query: str = "is:unread", max_results: int = 10) -> dict:
        headers = await google_oauth.auth_headers()
        params = {"q": query or "is:unread", "maxResults": max(1, min(max_results, 25))}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/messages", headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
            messages = payload.get("messages", [])

            emails = []
            for item in messages:
                detail = await client.get(
                    f"{self.base_url}/messages/{item['id']}",
                    headers=headers,
                    params={
                        "format": "metadata",
                        "metadataHeaders": ["From", "Subject", "Date"],
                    },
                )
                detail.raise_for_status()
                message = detail.json()
                metadata = {
                    header["name"].lower(): header["value"]
                    for header in message.get("payload", {}).get("headers", [])
                }
                emails.append({
                    "id": message.get("id"),
                    "thread_id": message.get("threadId"),
                    "from": metadata.get("from", ""),
                    "subject": metadata.get("subject", ""),
                    "date": metadata.get("date", ""),
                    "snippet": message.get("snippet", ""),
                })

        return {
            "query": params["q"],
            "count_returned": len(emails),
            "estimated_total": payload.get("resultSizeEstimate", len(emails)),
            "emails": emails,
        }

    async def get_email(self, message_id: str) -> dict:
        headers = await google_oauth.auth_headers()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/messages/{message_id}",
                headers=headers,
                params={"format": "full"},
            )
            response.raise_for_status()
            return response.json()

    async def send_email(self, to: str, subject: str, body: str) -> dict:
        headers = await google_oauth.auth_headers()
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/messages/send",
                headers=headers,
                json={"raw": raw},
            )
            response.raise_for_status()
            return response.json()


class CalendarClient:
    base_url = "https://www.googleapis.com/calendar/v3"

    def is_configured(self) -> bool:
        return google_oauth.is_configured() and google_oauth.has_refresh_token()

    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int = 10,
    ) -> dict:
        headers = await google_oauth.auth_headers()
        params = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": max(1, min(max_results, 25)),
            "timeMin": time_min or datetime.now(timezone.utc).isoformat(),
        }
        if time_max:
            params["timeMax"] = time_max

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/calendars/{calendar_id}/events",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def schedule_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        calendar_id: str = "primary",
        timezone_name: str = "Asia/Kolkata",
        description: str = "",
    ) -> dict:
        headers = await google_oauth.auth_headers()
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": timezone_name},
            "end": {"dateTime": end_time, "timeZone": timezone_name},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/calendars/{calendar_id}/events",
                headers=headers,
                json=event,
            )
            response.raise_for_status()
            return response.json()


google_oauth = GoogleOAuthClient()
gmail_client = GmailClient()
calendar_client = CalendarClient()
