"""
API Client for connecting the Qt app to a remote Budgie server.

Drop-in replacement for Database when a server_url is configured.
Uses only stdlib (urllib.request) to avoid extra dependencies.
"""

import json
import os
import sqlite3
import urllib.request
import urllib.error
from datetime import date, datetime
from typing import Optional

from database.profile import Profile
from database.account import Account
from database.budget_group import BudgetGroup
from database.budget_item import BudgetItem
from database.budget_item_period import BudgetItemPeriod
from database.extrapolation_item import ExtrapolationItem
from database.ledger_entry import LedgerEntry
from database.debt import Debt


class ApiClient:
    """HTTP-based replacement for Database that talks to the FastAPI server."""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        # Cache: maps account_id -> profile_id for efficient ledger lookups
        self._account_profile_cache: dict[int, int] = {}
        # Local SQLite for app-level settings only (last_profile_id, etc.)
        self._init_local_settings_db()

    # ========================================================================
    # HTTP helper
    # ========================================================================

    def _request(self, method: str, path: str, body=None) -> dict | list | None:
        """Make an HTTP request and return parsed JSON (or None for 204)."""
        url = f"{self.server_url}{path}"
        data = None
        if body is not None:
            data = json.dumps(body, default=str).encode("utf-8")

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = resp.read()
                if not resp_data:
                    return None
                return json.loads(resp_data)
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"API error {e.code} {method} {path}: {body_text}"
            ) from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach server at {self.server_url}: {e.reason}"
            ) from e

    # ========================================================================
    # Local settings DB (tiny SQLite for app-level prefs)
    # ========================================================================

    def _init_local_settings_db(self):
        config_dir = os.path.join(
            os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
            "budgie",
        )
        os.makedirs(config_dir, exist_ok=True)
        self._settings_db_path = os.path.join(config_dir, "budgie_settings.db")
        conn = sqlite3.connect(self._settings_db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.commit()
        conn.close()

    def _settings_conn(self):
        return sqlite3.connect(self._settings_db_path)

    def get_setting(self, key: str) -> str | None:
        conn = self._settings_conn()
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        conn.close()
        return row[0] if row else None

    def set_setting(self, key: str, value: str):
        conn = self._settings_conn()
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
        conn.close()

    def get_last_profile_id(self) -> int | None:
        val = self.get_setting("last_profile_id")
        return int(val) if val else None

    def set_last_profile_id(self, profile_id: int):
        self.set_setting("last_profile_id", str(profile_id))

    # ========================================================================
    # JSON -> Model conversion helpers
    # ========================================================================

    @staticmethod
    def _parse_profile(d: dict) -> Profile:
        hidden_through = None
        if d.get("hidden_through"):
            try:
                hidden_through = date.fromisoformat(d["hidden_through"][:10])
            except (ValueError, TypeError):
                pass
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        return Profile(
            name=d["name"],
            id=d["id"],
            created_at=created_at,
            hidden_through=hidden_through,
            theme=d.get("theme", "dark"),
        )

    @staticmethod
    def _parse_account(d: dict) -> Account:
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if d.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(d["updated_at"])
            except (ValueError, TypeError):
                pass
        acc = Account(
            name=d["name"],
            account_type=d.get("type", ""),
            id=d.get("id"),
            created_at=created_at,
            updated_at=updated_at,
        )
        acc.balance = d.get("balance", 0)
        # Parse ledger entries if present
        if "ledger" in d and d["ledger"]:
            acc.ledger = [ApiClient._parse_ledger_entry(le) for le in d["ledger"]]
        return acc

    @staticmethod
    def _parse_budget_group(d: dict) -> BudgetGroup:
        if isinstance(d, dict):
            return BudgetGroup(name=d.get("name", ""), id=d.get("id"))
        # Sometimes the API returns just a string name
        return BudgetGroup(name=str(d))

    @staticmethod
    def _parse_budget_item_period(d: dict) -> BudgetItemPeriod:
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if d.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(d["updated_at"])
            except (ValueError, TypeError):
                pass
        return BudgetItemPeriod(
            type=d.get("type", ""),
            value=d.get("value", ""),
            business_day=d.get("businessDay") or d.get("business_day"),
            budget_item_id=d.get("budget_item_id"),
            id=d.get("id"),
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _parse_budget_item(d: dict) -> BudgetItem:
        periods = []
        for p in d.get("periods", []):
            periods.append(ApiClient._parse_budget_item_period(p))

        start_date = None
        if d.get("start_date"):
            try:
                start_date = date.fromisoformat(d["start_date"][:10])
            except (ValueError, TypeError):
                pass
        end_date = None
        if d.get("end_date"):
            try:
                end_date = date.fromisoformat(d["end_date"][:10])
            except (ValueError, TypeError):
                pass
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if d.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(d["updated_at"])
            except (ValueError, TypeError):
                pass

        return BudgetItem(
            name=d["name"],
            type=d.get("type", ""),
            amount=d.get("amount", 0),
            start_date=start_date,
            end_date=end_date,
            budget_group_id=d.get("budget_group_id"),
            periods=periods,
            id=d.get("id"),
            created_at=created_at,
            updated_at=updated_at,
            debt_id=d.get("debt_id"),
        )

    @staticmethod
    def _parse_ledger_entry(d: dict) -> LedgerEntry:
        paid_date = None
        if d.get("paid_date"):
            try:
                paid_date = datetime.fromisoformat(d["paid_date"])
            except (ValueError, TypeError):
                pass
        income_date = None
        if d.get("income_date"):
            try:
                income_date = datetime.fromisoformat(d["income_date"])
            except (ValueError, TypeError):
                pass
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if d.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(d["updated_at"])
            except (ValueError, TypeError):
                pass
        return LedgerEntry(
            name=d.get("name", ""),
            paid_date=paid_date,
            income_date=income_date,
            type=d.get("type", ""),
            amount=d.get("amount", 0),
            account_id=d.get("account_id"),
            id=d.get("id"),
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _parse_extrapolation_item(d: dict) -> ExtrapolationItem:
        due_date = None
        if d.get("due_date"):
            try:
                due_date = date.fromisoformat(str(d["due_date"])[:10])
            except (ValueError, TypeError):
                pass
        income_date = None
        if d.get("income_date"):
            try:
                income_date = date.fromisoformat(str(d["income_date"])[:10])
            except (ValueError, TypeError):
                pass
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if d.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(d["updated_at"])
            except (ValueError, TypeError):
                pass
        return ExtrapolationItem(
            due_date=due_date,
            amount=d.get("amount", 0),
            income_date=income_date,
            budget_item_id=d.get("budget_item_id"),
            overridden_at=d.get("overridden_at"),
            ledger_entry_id=d.get("ledger_entry_id"),
            id=d.get("id"),
            created_at=created_at,
            updated_at=updated_at,
            category=d.get("category"),
            name=d.get("name"),
        )

    @staticmethod
    def _parse_debt(d: dict) -> Debt:
        created_at = None
        if d.get("created_at"):
            try:
                created_at = datetime.fromisoformat(d["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if d.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(d["updated_at"])
            except (ValueError, TypeError):
                pass
        return Debt(
            name=d.get("name", ""),
            total_amount=d.get("total_amount", 0),
            remaining_amount=d.get("remaining_amount", 0),
            min_payment=d.get("min_payment", 0),
            interest_rate=d.get("interest_rate", 0),
            profile_id=d.get("profile_id"),
            id=d.get("id"),
            created_at=created_at,
            updated_at=updated_at,
        )

    # ========================================================================
    # Profile methods
    # ========================================================================

    def fetch_profiles(self) -> list[Profile]:
        data = self._request("GET", "/profiles")
        return [self._parse_profile(d) for d in data]

    def create_profile(self, name) -> Profile:
        data = self._request("POST", "/profiles", {"name": name})
        return self._parse_profile(data)

    def delete_profile(self, profile_id):
        self._request("DELETE", f"/profiles/{profile_id}")

    def get_profile_by_id(self, profile_id: int) -> Profile | None:
        try:
            data = self._request("GET", f"/profiles/{profile_id}")
            return self._parse_profile(data)
        except RuntimeError:
            return None

    def update_profile_hidden_through(self, profile_id: int, hidden_through: str):
        self._request(
            "PUT",
            f"/profiles/{profile_id}/hidden_through",
            {"hidden_through": hidden_through},
        )

    def update_profile_theme(self, profile_id: int, theme: str):
        self._request(
            "PUT",
            f"/profiles/{profile_id}/theme",
            {"theme": theme},
        )

    # ========================================================================
    # Account methods
    # ========================================================================

    def fetch_accounts(self, profileId) -> list[Account]:
        # The profile endpoint includes accounts — fetch profile and extract
        data = self._request("GET", f"/profiles/{profileId}")
        accounts = []
        for a in data.get("accounts", []):
            acc = self._parse_account(a)
            accounts.append(acc)
            # Cache account->profile mapping for ledger lookups
            if acc.id is not None:
                self._account_profile_cache[acc.id] = profileId
        return accounts

    def create_account(self, profileId, name, account_type, balance) -> Account:
        data = self._request(
            "POST",
            f"/accounts/{profileId}",
            {"name": name, "type": account_type, "balance": balance},
        )
        return self._parse_account(data)

    def update_account(self, account_id, name, account_type, balance):
        # The server endpoint requires profile_id in the URL.
        # We pass 0 as a placeholder since the server ignores it for update.
        data = self._request(
            "PUT",
            f"/accounts/0/{account_id}",
            {"name": name, "type": account_type, "balance": balance},
        )
        return self._parse_account(data)

    def delete_account(self, account_id):
        # Server endpoint requires profile_id; use 0 as placeholder
        self._request("DELETE", f"/accounts/0/{account_id}")

    def update_account_balance(self, account_id, amount_delta):
        # Balance is tracked via ledger entries — no-op like Database
        pass

    # ========================================================================
    # Budget group methods
    # ========================================================================

    def fetch_budget_groups(self, profileId) -> list[BudgetGroup]:
        data = self._request("GET", f"/profiles/{profileId}")
        groups = []
        for g in data.get("budget_groups", []):
            if isinstance(g, dict):
                groups.append(self._parse_budget_group(g))
            else:
                # budget_groups might be returned as simple dicts or other shapes
                groups.append(BudgetGroup(name=str(g)))
        return groups

    def create_budget_group(self, profileId, name) -> BudgetGroup:
        data = self._request(
            "POST", f"/budget/group/{profileId}", {"name": name}
        )
        return BudgetGroup(name=data.get("name", name), id=data.get("id"))

    def delete_budget_group(self, group_id):
        # Server endpoint requires profile_id; use 0 as placeholder
        self._request("DELETE", f"/budget/group/0/{group_id}")

    # ========================================================================
    # Budget item methods
    # ========================================================================

    def fetch_budget_items(self, profileId) -> list[BudgetItem]:
        data = self._request("GET", f"/profiles/{profileId}")
        items = []
        for b in data.get("budget_items", []):
            items.append(self._parse_budget_item(b))
        return items

    def fetch_budget_item_periods(self, itemId) -> list[BudgetItemPeriod]:
        # Periods come with budget items; re-fetch the item via its profile
        # This is a less common call — return empty if we can't determine profile
        return []

    def _resolve_budget_group_id(self, profile_id, group):
        """Resolve a group name string to its integer ID."""
        if group is None or isinstance(group, int):
            return group
        if isinstance(group, str):
            try:
                return int(group)
            except ValueError:
                pass
            groups = self.fetch_budget_groups(profile_id)
            match = next((g for g in groups if g.name == group), None)
            return match.id if match else None
        return group

    def create_budget_item(
        self, profileId, name, type, amount, group, start_date, end_date, periods, debt_id=None
    ):
        group_id = self._resolve_budget_group_id(profileId, group)
        period_dicts = []
        for p in periods:
            if hasattr(p, "type"):
                period_dicts.append({
                    "type": p.type,
                    "value": p.value,
                    "business_day": p.business_day,
                })
            else:
                period_dicts.append(p)

        data = self._request(
            "POST",
            f"/budget/{profileId}",
            {
                "name": name,
                "type": type,
                "amount": amount,
                "budget_group_id": group_id,
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
                "periods": period_dicts,
                "debt_id": debt_id,
            },
        )
        return self._parse_budget_item(data)

    def update_budget_item(
        self, budget_item_id, name, type, amount, group, start_date, end_date, periods, debt_id=None
    ):
        # Need profile_id for the URL — try to resolve group which might tell us
        # Use 0 as placeholder; server uses budget_item_id for the actual lookup
        group_id = group if isinstance(group, int) else None
        if isinstance(group, str):
            try:
                group_id = int(group)
            except ValueError:
                group_id = None

        period_dicts = []
        for p in periods:
            if hasattr(p, "type"):
                period_dicts.append({
                    "type": p.type,
                    "value": p.value,
                    "business_day": p.business_day,
                })
            else:
                period_dicts.append(p)

        data = self._request(
            "PUT",
            f"/budget/0/{budget_item_id}",
            {
                "name": name,
                "type": type,
                "amount": amount,
                "budget_group_id": group_id,
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
                "periods": period_dicts,
                "debt_id": debt_id,
            },
        )
        return self._parse_budget_item(data)

    def delete_budget_item(self, budget_item_id):
        self._request("DELETE", f"/budget/0/{budget_item_id}")

    # ========================================================================
    # Ledger methods
    # ========================================================================

    def fetch_ledger_items(self, accountId) -> list[LedgerEntry]:
        # Ledger entries are nested in account data from the profile endpoint.
        # Use the cache to find the profile_id, falling back to scanning profiles.
        profile_id = self._account_profile_cache.get(accountId)
        if profile_id is not None:
            data = self._request("GET", f"/profiles/{profile_id}")
            for acc in data.get("accounts", []):
                if acc.get("id") == accountId:
                    return [self._parse_ledger_entry(le) for le in acc.get("ledger", [])]

        # Fallback: scan all profiles
        profiles = self.fetch_profiles()
        for profile in profiles:
            data = self._request("GET", f"/profiles/{profile.id}")
            for acc in data.get("accounts", []):
                if acc.get("id") == accountId:
                    self._account_profile_cache[accountId] = profile.id
                    return [self._parse_ledger_entry(le) for le in acc.get("ledger", [])]
        return []

    def create_ledger_entry(
        self, name, date_val, incomeDate, type, amount, accountId
    ) -> LedgerEntry:
        data = self._request(
            "POST",
            f"/ledger/0",
            {
                "account_id": accountId,
                "amount": amount,
                "date": str(date_val) if date_val else None,
                "income_date": str(incomeDate) if incomeDate else None,
                "notes": name,
            },
        )
        return self._parse_ledger_entry(data)

    def get_ledger_entry(self, ledger_item_id):
        # No dedicated endpoint — would need to search through profiles
        # Return None for now; callers handle this gracefully
        return None

    def update_ledger_entry(self, ledger_item_id, name, date_val, income_date, amount, account_id):
        data = self._request(
            "PUT",
            f"/ledger/0/{ledger_item_id}",
            {
                "account_id": account_id,
                "amount": amount,
                "date": str(date_val) if date_val else None,
                "income_date": str(income_date) if income_date else None,
                "notes": name,
            },
        )
        return self._parse_ledger_entry(data)

    def delete_ledger_entry(self, ledger_item_id):
        self._request("DELETE", f"/ledger/0/{ledger_item_id}")

    # ========================================================================
    # Extrapolation methods
    # ========================================================================

    def fetch_extrapolation_items(self, profileId) -> list[ExtrapolationItem]:
        data = self._request("GET", f"/schedule/{profileId}")
        items = []
        # The schedule endpoint returns a different shape — extrapolation items
        # are nested under columns. Fall back to getting from profile data.
        if isinstance(data, dict):
            # Try to extract extrapolation items from schedule data
            for col in data.get("columns", []):
                for item in col.get("items", []):
                    items.append(self._parse_extrapolation_item(item))
            # Also check unscheduled items
            for item in data.get("unscheduled", []):
                items.append(self._parse_extrapolation_item(item))
        elif isinstance(data, list):
            for item in data:
                items.append(self._parse_extrapolation_item(item))
        return items

    def create_extrapolation_item(
        self, profileId, date_val, amount, income_date, budget_item_id, category=None, name=None
    ):
        data = self._request(
            "POST",
            f"/extrapolation/{profileId}/item",
            {
                "due_date": str(date_val) if date_val else None,
                "amount": amount,
                "income_date": str(income_date) if income_date else None,
                "budget_item_id": budget_item_id,
                "category": category,
                "name": name,
            },
        )
        return self._parse_extrapolation_item(data)

    def clear_extrapolation_items(self, profileId):
        self._request("DELETE", f"/extrapolation/{profileId}")

    def clear_unpaid_extrapolation_items(self, profileId):
        self._request("DELETE", f"/extrapolation/{profileId}/unpaid")

    def update_extrapolation_item(self, item_id, amount=None, date_val=None):
        body = {}
        if amount is not None:
            body["amount"] = amount
        if date_val is not None:
            body["date"] = str(date_val)
        # Use the existing update endpoint
        if "amount" in body and "date" in body:
            data = self._request(
                "PUT",
                f"/extrapolate/updateitem/{item_id}",
                {"amount": body["amount"], "date": body["date"]},
            )
        elif "amount" in body:
            data = self._request(
                "PUT",
                f"/extrapolate/updateitem/{item_id}",
                {"amount": body["amount"], "date": "1970-01-01"},
            )
        elif "date" in body:
            data = self._request(
                "PUT",
                f"/extrapolate/updateitem/{item_id}",
                {"amount": 0, "date": body["date"]},
            )
        else:
            return None
        return self._parse_extrapolation_item(data) if data else None

    def update_extrapolation_item_ledger_id(self, extrapolation_item_id, ledger_entry_id):
        self._request(
            "PUT",
            f"/extrapolation/item/{extrapolation_item_id}/ledger_id",
            {"ledger_entry_id": ledger_entry_id},
        )

    def update_extrapolation_item_income_date(self, item_id, income_date):
        self._request(
            "PUT",
            f"/extrapolation/item/{item_id}/income_date",
            {"income_date": str(income_date) if income_date else None},
        )

    def get_extrapolation_item(self, item_id):
        # No dedicated GET endpoint — return None
        return None

    def move_extrapolation_items(self, profile_id, budget_item_id, from_income_date, to_income_date):
        data = self._request(
            "POST",
            f"/calendar/{profile_id}/move_item",
            {
                "budget_item_id": budget_item_id,
                "from_income_date": str(from_income_date),
                "to_income_date": str(to_income_date),
            },
        )
        return data.get("count", 0) if data else 0

    def split_extrapolation_item(self, item_id, keep_amount, remainder_income_date=None):
        data = self._request(
            "POST",
            f"/calendar/0/split_item",
            {
                "extrapolation_item_id": item_id,
                "keep_amount": keep_amount,
                "remainder_income_date": str(remainder_income_date) if remainder_income_date else None,
            },
        )
        return data if data else {}

    # ========================================================================
    # Debt methods
    # ========================================================================

    def fetch_debts(self, profileId) -> list[Debt]:
        data = self._request("GET", f"/debts/{profileId}")
        return [self._parse_debt(d) for d in data]

    def create_debt(self, profileId, name, total_amount, remaining_amount, min_payment, interest_rate) -> Debt:
        data = self._request(
            "POST",
            f"/debts/{profileId}",
            {
                "name": name,
                "total_amount": total_amount,
                "remaining_amount": remaining_amount,
                "min_payment": min_payment,
                "interest_rate": interest_rate,
            },
        )
        return self._parse_debt(data)

    def update_debt(self, debt_id, name, total_amount, remaining_amount, min_payment, interest_rate):
        data = self._request(
            "PUT",
            f"/debts/0/{debt_id}",
            {
                "name": name,
                "total_amount": total_amount,
                "remaining_amount": remaining_amount,
                "min_payment": min_payment,
                "interest_rate": interest_rate,
            },
        )
        return self._parse_debt(data)

    def delete_debt(self, debt_id):
        self._request("DELETE", f"/debts/0/{debt_id}")

    # ========================================================================
    # Export / Import
    # ========================================================================

    def export_profile(self, profile_id: int) -> dict:
        """Export a profile as JSON dict via the server API."""
        data = self._request("GET", f"/profile/{profile_id}/export")
        return data

    def import_profile(self, import_data: dict) -> dict:
        """Import a profile from a JSON dict via the server API."""
        data = self._request("POST", "/profiles/import", import_data)
        return data
