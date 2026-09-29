"""Account-type behavior shared by the accounts API and financial summaries."""
from datetime import date

from httpx import AsyncClient

from tests.helpers import money, txn_payload


async def test_debit_card_is_a_liquid_account_type(client: AsyncClient, categories):
    response = await client.post(
        "/accounts",
        json={"name": "Debit card", "type": "debit_card", "currency": "RUB"},
    )

    assert response.status_code == 201
    debit_card = response.json()
    assert debit_card["type"] == "debit_card"

    transaction = await client.post(
        "/transactions",
        json=txn_payload(
            debit_card["id"],
            type="income",
            amount="1000.00",
            category_id=categories["Salary"]["id"],
            date=date.today().isoformat(),
        ),
    )
    assert transaction.status_code == 201

    summary = await client.get("/net-worth/summary", params={"range": "all"})

    assert summary.status_code == 200
    assert money(summary.json()["current"]) == money("1000.00")


async def test_primary_account_sorts_first_and_is_exclusive(client: AsyncClient):
    first = await client.post(
        "/accounts",
        json={"name": "Zulu", "type": "checking", "currency": "USD", "is_primary": True},
    )
    second = await client.post(
        "/accounts",
        json={"name": "Alpha", "type": "checking", "currency": "USD"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["is_primary"] is True
    assert second.json()["is_primary"] is False

    listed = await client.get("/accounts")
    assert listed.status_code == 200
    names = [row["name"] for row in listed.json() if row["name"] in {"Zulu", "Alpha"}]
    assert names[0] == "Zulu"

    # Promoting Alpha clears Zulu's flag and puts Alpha first.
    promoted = await client.patch(
        f"/accounts/{second.json()['id']}",
        json={"is_primary": True},
    )
    assert promoted.status_code == 200
    assert promoted.json()["is_primary"] is True

    listed_again = await client.get("/accounts")
    rows = {row["name"]: row for row in listed_again.json() if row["name"] in {"Zulu", "Alpha"}}
    assert rows["Alpha"]["is_primary"] is True
    assert rows["Zulu"]["is_primary"] is False
    ordered = [row["name"] for row in listed_again.json() if row["name"] in {"Zulu", "Alpha"}]
    assert ordered[0] == "Alpha"

    # Archiving the primary drops the flag.
    archived = await client.patch(
        f"/accounts/{second.json()['id']}",
        json={"is_archived": True},
    )
    assert archived.status_code == 200
    assert archived.json()["is_primary"] is False
