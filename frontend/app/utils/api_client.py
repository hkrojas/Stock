from __future__ import annotations

import os
import re
from datetime import date, datetime
from typing import Any

import requests
from flask import current_app, session


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _normalize_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    if ISO_DATETIME_RE.match(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

    if ISO_DATE_RE.match(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return value

    return value


def _normalize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: _normalize_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_normalize_payload(item) for item in payload]
    return _normalize_scalar(payload)


# Module level session for connection pooling across APIClient instances
_shared_session = requests.Session()


class APIClient:
    """HTTP client for Flask -> FastAPI calls using the access token issued by FastAPI."""

    def __init__(self, user_id: int | None = None, token: str | None = None):
        del user_id
        self.base_url = current_app.config.get(
            "API_BASE_URL",
            os.getenv("API_BASE_URL", "http://localhost:8000/api/v1"),
        ).rstrip("/")
        self.token = token or session.get("access_token")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        return_response: bool = False,
        stream: bool = False,
    ) -> Any:
        # Use headers but don't modify the shared session's own headers
        request_headers = self.headers.copy()
        if files:
            request_headers.pop("Content-Type", None)

        # Call with shared session to reuse TCP connections
        response = _shared_session.request(
            method,
            f"{self.base_url}{path}",
            headers=request_headers,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=30,
            stream=stream,
        )
        response.raise_for_status()

        if return_response:
            return response

        if not response.content:
            return None

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return _normalize_payload(response.json())

        return response.text

    def get(
        self,
        path: str,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        *,
        return_response: bool = False,
        stream: bool = False,
    ) -> Any:
        return self._request("GET", path, params=params, return_response=return_response, stream=stream)

    def post(
        self,
        path: str,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        return_response: bool = False,
        stream: bool = False,
    ) -> Any:
        return self._request(
            "POST",
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            return_response=return_response,
            stream=stream,
        )

    def put(
        self,
        path: str,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        return_response: bool = False,
        stream: bool = False,
    ) -> Any:
        return self._request(
            "PUT",
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            return_response=return_response,
            stream=stream,
        )

    def patch(
        self,
        path: str,
        json: Any = None,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        return_response: bool = False,
    ) -> Any:
        return self._request("PATCH", path, params=params, json=json, return_response=return_response)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        return_response: bool = False,
    ) -> Any:
        return self._request("DELETE", path, params=params, return_response=return_response)

    @staticmethod
    def error_detail(exc: requests.HTTPError) -> str:
        try:
            return exc.response.json().get("detail", str(exc))
        except Exception:
            return str(exc)
