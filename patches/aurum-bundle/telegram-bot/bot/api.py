"""Thin httpx client for the Aurum REST API (accounts / categories / txns)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from bot.config import get_settings


class AurumApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AurumClient:
    def __init__(self) -> None:
        settings = get_settings()
        auth = None
        pair = settings.api_basic_auth()
        if pair:
            auth = httpx.BasicAuth(pair[0], pair[1])

        self._client = httpx.AsyncClient(
            base_url=settings.telegram_api_base.rstrip("/"),
            auth=auth,
            timeout=30.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str) -> Any:
        response = await self._client.get(path)
        if response.status_code >= 400:
            raise AurumApiError(f"GET {path} → {response.status_code}: {response.text}", response.status_code)
        return response.json()

    async def _post(self, path: str, payload: dict[str, Any]) -> Any:
        response = await self._client.post(path, json=payload)
        if response.status_code >= 400:
            raise AurumApiError(f"POST {path} → {response.status_code}: {response.text}", response.status_code)
        return response.json()

    async def health(self) -> bool:
        try:
            data = await self._get("/health")
            return data.get("status") == "ok"
        except Exception:
            return False

    async def list_accounts(self) -> list[dict[str, Any]]:
        rows = await self._get("/accounts")
        return [row for row in rows if not row.get("is_archived")]

    async def list_expense_categories(self) -> list[dict[str, Any]]:
        rows = await self._get("/categories")
        # Top-level expense categories only — keeps the inline keyboard short.
        return [
            row
            for row in rows
            if row.get("kind") == "expense" and row.get("parent_id") is None
        ]

    async def create_expense(
        self,
        *,
        account_id: int,
        category_id: int,
        amount: Decimal,
        description: str,
        when: date | None = None,
    ) -> dict[str, Any]:
        payload = {
            "account_id": account_id,
            "category_id": category_id,
            "transfer_account_id": None,
            "type": "expense",
            "amount": str(amount),
            "description": description,
            "date": (when or date.today()).isoformat(),
            "tag_ids": [],
        }
        return await self._post("/transactions", payload)
