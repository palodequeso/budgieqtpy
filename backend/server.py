"""
Fast-API Server
"""

import os
from typing import Optional, List
from datetime import date, datetime, timedelta
import tempfile

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database.database import Database
from services import (
    ProfileService,
    AccountService,
    BudgetService,
    LedgerService,
    CalendarService,
    AIService,
    DebtService,
    ReconciliationService
)

# ============================================================================
# Serialization Helper Functions
# ============================================================================

def serialize_profile(profile) -> dict:
    """Convert Profile object to dict for JSON responses."""
    return {
        "id": profile.id,
        "name": profile.name,
        "hidden_through": profile.hidden_through.isoformat() if profile.hidden_through else None,
        "created_at": profile.created_at.isoformat() if hasattr(profile.created_at, 'isoformat') else str(profile.created_at),
        "accounts": [serialize_account(a) for a in getattr(profile, 'accounts', [])],
        "budget_groups": getattr(profile, 'budget_groups', []),
        "budget_items": [serialize_budget_item(b) for b in getattr(profile, 'budget_items', [])],
    }

def serialize_account(account) -> dict:
    """Serialize account object."""
    ledger_entries = []
    calculated_balance = 0.0
    
    if hasattr(account, 'ledger') and account.ledger:
        ledger_entries = [serialize_ledger_entry(le) for le in account.ledger]
        # Calculate balance from ledger entries (this is the correct way)
        for entry in account.ledger:
            calculated_balance += float(entry.amount) if entry.amount else 0.0
    
    return {
        "id": account.id,
        "name": account.name,
        "type": account.account_type,
        "balance": calculated_balance,
        "ledger": ledger_entries,
    }

def serialize_ledger_entry(entry) -> dict:
    """Serialize ledger entry object."""
    return {
        "id": entry.id,
        "name": entry.name,
        "paid_date": entry.paid_date.isoformat() if hasattr(entry.paid_date, 'isoformat') else str(entry.paid_date),
        "income_date": entry.income_date.isoformat() if hasattr(entry.income_date, 'isoformat') else str(entry.income_date),
        "type": entry.type,
        "amount": float(entry.amount) if entry.amount else 0.0,
        "account_id": entry.account_id,
        "created_at": entry.created_at.isoformat() if hasattr(entry.created_at, 'isoformat') else None,
        "updated_at": entry.updated_at.isoformat() if hasattr(entry.updated_at, 'isoformat') else None,
    }

def serialize_budget_item(item) -> dict:
    """Serialize budget item object."""
    periods = []
    if hasattr(item, 'periods') and item.periods:
        periods = [
            {
                "id": p.id if hasattr(p, 'id') else None,
                "type": p.type,
                "value": p.value,
                "businessDay": p.business_day if hasattr(p, 'business_day') else None,
            }
            for p in item.periods
        ]
    
    return {
        "id": item.id,
        "name": item.name,
        "amount": float(item.amount) if item.amount else 0.0,
        "type": item.type,
        "start_date": item.start_date.isoformat() if hasattr(item.start_date, 'isoformat') else str(item.start_date) if item.start_date else None,
        "end_date": item.end_date.isoformat() if hasattr(item.end_date, 'isoformat') else str(item.end_date) if item.end_date else None,
        "budget_group_id": item.budget_group_id,
        "debt_id": item.debt_id if hasattr(item, 'debt_id') else None,
        "periods": periods,
        "created_at": item.created_at.isoformat() if hasattr(item, 'created_at') and hasattr(item.created_at, 'isoformat') else None,
        "updated_at": item.updated_at.isoformat() if hasattr(item, 'updated_at') and hasattr(item.updated_at, 'isoformat') else None,
    }

# ============================================================================
# Pydantic Models for Request/Response Validation
# ============================================================================

class ProfileCreate(BaseModel):
    name: str

class AccountCreate(BaseModel):
    name: str
    type: str
    balance: float

class BudgetPeriod(BaseModel):
    type: str
    value: str
    business_day: Optional[str] = None

class BudgetItemCreate(BaseModel):
    name: str
    amount: float
    type: str
    budget_group_id: int
    start_date: str
    end_date: str
    periods: List[BudgetPeriod]
    debt_id: Optional[int] = None

class BudgetGroupCreate(BaseModel):
    name: str

class LedgerItemCreate(BaseModel):
    account_id: int
    amount: float
    date: str
    income_date: str
    budget_item_id: Optional[int] = None
    notes: Optional[str] = None

class ExtrapolateRequest(BaseModel):
    profileID: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ExtrapolationItemUpdate(BaseModel):
    amount: float
    date: str

class MarkPaidRequest(BaseModel):
    extrapolationItemId: int
    accountId: int

class OneOffRequest(BaseModel):
    name: str
    amount: float
    type: str
    incomeDate: str
    account: Optional[int] = None
    addingOneOffExpensePaid: bool = False

class ComputeSavingsRequest(BaseModel):
    savingsAccount: int
    spendingBuffer: float

class SavedSavingsEntry(BaseModel):
    date: str
    amount: float

class SaveComputedSavingsRequest(BaseModel):
    addedEntries: List[SavedSavingsEntry]
    savingsAccount: int

class FixUnscheduledItem(BaseModel):
    id: int
    income_date: str

class MoveItemRequest(BaseModel):
    budget_item_id: int
    from_income_date: str
    to_income_date: str

class SplitItemRequest(BaseModel):
    extrapolation_item_id: int
    keep_amount: float
    remainder_income_date: Optional[str] = None  # if None, stays in same column

class DownloadSpreadsheetRequest(BaseModel):
    filePath: Optional[str] = None

class DebtCreate(BaseModel):
    name: str
    total_amount: float
    remaining_amount: float
    min_payment: float = 0.0
    interest_rate: float = 0.0

class ComputeDebtPaymentsRequest(BaseModel):
    savings_margin: float = 0.0

class DebtPaymentEntry(BaseModel):
    debt_id: int
    debt_name: str
    amount: float
    income_date: str

class SaveDebtPaymentsRequest(BaseModel):
    payments: List[DebtPaymentEntry]

class AIConfigUpdate(BaseModel):
    server_url: str
    model: str
    enabled: bool

class ReconcileParseRequest(BaseModel):
    csv_content: str
    date_col: Optional[str] = None
    amount_col: Optional[str] = None
    desc_col: Optional[str] = None

class ReconcileMatchRequest(BaseModel):
    transactions: list
    account_id: int
    date_tolerance_days: int = 5
    amount_tolerance_pct: float = 0.10

class ReconcileConfirmItem(BaseModel):
    transaction: dict
    extrapolation_item_id: Optional[int] = None
    amount_override: Optional[float] = None

class ReconcileImportRequest(BaseModel):
    account_id: int
    confirmed: List[ReconcileConfirmItem]

class ThemeUpdate(BaseModel):
    theme: str

class SettingUpdate(BaseModel):
    value: str

class ExtrapolationItemCreate(BaseModel):
    due_date: str
    amount: float
    income_date: Optional[str] = None
    budget_item_id: Optional[int] = None
    category: Optional[str] = None
    name: Optional[str] = None

class ExtrapolationIncomeDateUpdate(BaseModel):
    income_date: str

class ExtrapolationLedgerIdUpdate(BaseModel):
    ledger_entry_id: Optional[int] = None

class ImportLedgerEntry(BaseModel):
    name: str
    paid_date: Optional[str] = None
    income_date: Optional[str] = None
    type: str
    amount: float

class ImportAccount(BaseModel):
    name: str
    account_type: str
    ledger_entries: List[ImportLedgerEntry] = []

class ImportBudgetGroup(BaseModel):
    name: str

class ImportBudgetPeriod(BaseModel):
    type: str
    value: str
    business_day: Optional[str] = None

class ImportBudgetItem(BaseModel):
    name: str
    type: str
    amount: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget_group_name: Optional[str] = None
    debt_name: Optional[str] = None
    periods: List[ImportBudgetPeriod] = []

class ImportDebt(BaseModel):
    name: str
    total_amount: float
    remaining_amount: float
    min_payment: float = 0.0
    interest_rate: float = 0.0

class ImportExtrapolationItem(BaseModel):
    due_date: Optional[str] = None
    amount: float
    income_date: Optional[str] = None
    budget_item_name: Optional[str] = None
    ledger_entry_linked: bool = False
    category: Optional[str] = None
    name: Optional[str] = None

class ImportProfile(BaseModel):
    name: str
    theme: Optional[str] = "dark"
    hidden_through: Optional[str] = None

class ImportRequest(BaseModel):
    version: int = 1
    exported_at: Optional[str] = None
    profile: ImportProfile
    accounts: List[ImportAccount] = []
    budget_groups: List[ImportBudgetGroup] = []
    budget_items: List[ImportBudgetItem] = []
    debts: List[ImportDebt] = []
    extrapolation_items: List[ImportExtrapolationItem] = []

# ============================================================================
# Server Class
# ============================================================================

class Server:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Profile Endpoints
    # ========================================================================

    @app.get("/profiles/{profile_id}")
    async def get_profile(profile_id: int):
        try:
            db = Database()
            service = ProfileService(db)
            profile = service.get_profile_by_id(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
            return serialize_profile(profile)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/profiles")
    async def get_profiles():
        try:
            db = Database()
            service = ProfileService(db)
            profiles = service.get_all_profiles()
            return [serialize_profile(p) for p in profiles]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/profiles")
    async def create_profile(profile: ProfileCreate):
        try:
            db = Database()
            service = ProfileService(db)
            new_profile = service.create_profile(profile.name)
            updated_at = getattr(new_profile, 'updated_at', None)
            return {
                "id": new_profile.id,
                "name": new_profile.name,
                "created_at": new_profile.created_at.isoformat() if new_profile.created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/profiles/{profile_id}")
    async def delete_profile(profile_id: int):
        try:
            db = Database()
            service = ProfileService(db)
            service.delete_profile(profile_id)
            return {"success": True, "id": profile_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/profiles/{profile_id}/hidden_through")
    async def update_profile_hidden_through(profile_id: int, request: dict):
        try:
            db = Database()
            hidden_through = request.get("hidden_through")
            db.update_profile_hidden_through(profile_id, hidden_through)
            return {"success": True, "hidden_through": hidden_through}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Account Endpoints
    # ========================================================================

    @app.post("/accounts/{profile_id}")
    async def create_account(profile_id: int, account: AccountCreate):
        try:
            db = Database()
            service = AccountService(db)
            new_account = service.create_account(
                profile_id=profile_id,
                name=account.name,
                account_type=account.type,
                balance=account.balance
            )
            return {
                "id": new_account.id,
                "name": new_account.name,
                "type": new_account.account_type,
                "balance": new_account.balance,
                "created_at": new_account.created_at.isoformat() if new_account.created_at else None,
                "updated_at": new_account.updated_at.isoformat() if new_account.updated_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/accounts/{profile_id}/{account_id}")
    async def update_account(profile_id: int, account_id: int, account: AccountCreate):
        try:
            db = Database()
            service = AccountService(db)
            updated_account = service.update_account(
                account_id=account_id,
                name=account.name,
                account_type=account.type,
                balance=account.balance
            )
            return {
                "id": updated_account.id,
                "name": updated_account.name,
                "type": updated_account.account_type,
                "balance": updated_account.balance,
                "updated_at": updated_account.updated_at.isoformat() if updated_account.updated_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/accounts/{profile_id}/{account_id}")
    async def delete_account(profile_id: int, account_id: int):
        try:
            db = Database()
            service = AccountService(db)
            service.delete_account(account_id)
            return {"success": True, "id": account_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Budget Item Endpoints
    # ========================================================================

    @app.post("/budget/{profile_id}")
    async def create_budget_item(profile_id: int, budget_item: BudgetItemCreate):
        try:
            db = Database()
            service = BudgetService(db)
            
            # Convert Pydantic models to dicts for service
            periods = [p.dict() for p in budget_item.periods]
            
            new_item = service.create_budget_item(
                profile_id=profile_id,
                name=budget_item.name,
                item_type=budget_item.type,
                amount=budget_item.amount,
                group_id=budget_item.budget_group_id,
                start_date=budget_item.start_date,
                end_date=budget_item.end_date,
                periods=periods,
                debt_id=budget_item.debt_id,
            )
            return {
                "id": new_item.id,
                "name": new_item.name,
                "type": new_item.type,
                "amount": new_item.amount,
                "budget_group_id": new_item.budget_group_id,
                "start_date": str(new_item.start_date) if new_item.start_date else None,
                "end_date": str(new_item.end_date) if new_item.end_date else None,
                "created_at": str(new_item.created_at) if new_item.created_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/budget/{profile_id}/{budget_item_id}")
    async def update_budget_item(profile_id: int, budget_item_id: int, budget_item: BudgetItemCreate):
        try:
            db = Database()
            service = BudgetService(db)
            
            # Convert Pydantic models to dicts for service
            periods = [p.dict() for p in budget_item.periods]
            
            updated_item = service.update_budget_item(
                budget_item_id=budget_item_id,
                name=budget_item.name,
                item_type=budget_item.type,
                amount=budget_item.amount,
                group_id=budget_item.budget_group_id,
                start_date=budget_item.start_date,
                end_date=budget_item.end_date,
                periods=periods,
                debt_id=budget_item.debt_id,
            )
            return {
                "id": updated_item.id,
                "name": updated_item.name,
                "type": updated_item.type,
                "amount": updated_item.amount,
                "updated_at": updated_item.updated_at.isoformat() if updated_item.updated_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/budget/{profile_id}/{budget_item_id}")
    async def delete_budget_item(profile_id: int, budget_item_id: int):
        try:
            db = Database()
            service = BudgetService(db)
            service.delete_budget_item(budget_item_id)
            return {"success": True, "id": budget_item_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Budget Group Endpoints
    # ========================================================================

    @app.post("/budget/group/{profile_id}")
    async def create_budget_group(profile_id: int, group: BudgetGroupCreate):
        try:
            db = Database()
            service = BudgetService(db)
            new_group = service.create_budget_group(profile_id, group.name)
            created_at = getattr(new_group, 'created_at', None)
            return {
                "id": new_group.id,
                "name": new_group.name,
                "created_at": created_at.isoformat() if created_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/budget/group/{profile_id}/{group_id}")
    async def delete_budget_group(profile_id: int, group_id: int):
        try:
            db = Database()
            service = BudgetService(db)
            service.delete_budget_group(group_id)
            return {"success": True, "id": group_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Ledger Endpoints
    # ========================================================================

    @app.post("/ledger/{profile_id}")
    async def create_ledger_entry(profile_id: int, ledger_item: LedgerItemCreate):
        try:
            db = Database()
            service = LedgerService(db)
            new_entry = service.create_ledger_entry(
                account_id=ledger_item.account_id,
                amount=ledger_item.amount,
                paid_date=ledger_item.date,
                income_date=ledger_item.income_date,
                name=ledger_item.notes or "Ledger Entry"
            )
            return {
                "id": new_entry.id,
                "name": new_entry.name,
                "amount": new_entry.amount,
                "date": new_entry.paid_date.isoformat() if hasattr(new_entry.paid_date, 'isoformat') else str(new_entry.paid_date),
                "account_id": new_entry.account_id,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/ledger/{profile_id}/{ledger_item_id}")
    async def update_ledger_entry(profile_id: int, ledger_item_id: int, ledger_item: LedgerItemCreate):
        try:
            db = Database()
            service = LedgerService(db)
            updated_entry = service.update_ledger_entry(
                ledger_item_id=ledger_item_id,
                account_id=ledger_item.account_id,
                amount=ledger_item.amount,
                paid_date=ledger_item.date,
                income_date=ledger_item.income_date,
                name=ledger_item.notes or "Ledger Entry"
            )
            return {
                "id": updated_entry.id,
                "name": updated_entry.name,
                "amount": updated_entry.amount,
                "updated_at": updated_entry.updated_at.isoformat() if updated_entry.updated_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/ledger/{profile_id}/{ledger_item_id}")
    async def delete_ledger_entry(profile_id: int, ledger_item_id: int):
        try:
            db = Database()
            service = LedgerService(db)
            service.delete_ledger_entry(ledger_item_id)
            return {"success": True, "id": ledger_item_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Dashboard Endpoint
    # ========================================================================

    @app.get("/dashboard/{profile_id}")
    async def get_dashboard(profile_id: int):
        """Aggregated dashboard data: upcoming, overdue, safe-to-spend, summary."""
        try:
            db = Database()
            today = date.today()
            week_ahead = today + timedelta(days=7)

            # Fetch all extrapolation items and budget items
            extrap_items = db.fetch_extrapolation_items(profile_id)
            budget_items = db.fetch_budget_items(profile_id)
            accounts = db.fetch_accounts(profile_id)
            budget_map = {bi.id: bi for bi in budget_items}

            def item_name(ei):
                if ei.name:
                    return ei.name
                if ei.budget_item_id and ei.budget_item_id in budget_map:
                    return budget_map[ei.budget_item_id].name
                return f"Item #{ei.id}"

            def item_type(ei):
                if ei.budget_item_id and ei.budget_item_id in budget_map:
                    return budget_map[ei.budget_item_id].type
                return "Expense"

            def serialize_item(ei):
                due = ei.due_date
                if isinstance(due, (date, datetime)):
                    due_str = due.strftime("%Y-%m-%d")
                elif due is not None:
                    due_str = str(due)[:10]
                else:
                    due_str = None

                inc = ei.income_date
                if isinstance(inc, (date, datetime)):
                    inc_str = inc.strftime("%Y-%m-%d")
                elif inc is not None:
                    inc_str = str(inc)[:10]
                else:
                    inc_str = None

                return {
                    "id": ei.id,
                    "name": item_name(ei),
                    "type": item_type(ei),
                    "amount": float(ei.amount) if ei.amount else 0,
                    "due_date": due_str,
                    "income_date": inc_str,
                    "budget_item_id": ei.budget_item_id,
                    "is_paid": ei.ledger_entry_id is not None,
                    "category": ei.category,
                }

            # Upcoming: due in next 7 days, not yet paid
            upcoming = []
            overdue = []
            for ei in extrap_items:
                if ei.ledger_entry_id is not None:
                    continue  # already paid
                due = ei.due_date
                if due is None:
                    continue
                if isinstance(due, str):
                    try:
                        due = date.fromisoformat(due[:10])
                    except (ValueError, TypeError):
                        continue
                elif isinstance(due, datetime):
                    due = due.date()
                if due < today:
                    overdue.append(serialize_item(ei))
                elif due <= week_ahead:
                    upcoming.append(serialize_item(ei))

            # Sort by due date
            upcoming.sort(key=lambda x: x["due_date"])
            overdue.sort(key=lambda x: x["due_date"])

            # Column summaries: group by income_date, compute totals
            columns = {}
            for ei in extrap_items:
                inc = ei.income_date
                if not inc:
                    continue
                key = inc.strftime("%Y-%m-%d") if isinstance(inc, (date, datetime)) else str(inc)[:10]
                if key not in columns:
                    columns[key] = {"income_date": key, "income": 0, "expenses": 0, "paid_expenses": 0}
                amt = float(ei.amount)
                etype = item_type(ei)
                if etype and etype.lower() == "income":
                    columns[key]["income"] += amt
                else:
                    columns[key]["expenses"] += abs(amt)
                    if ei.ledger_entry_id is not None:
                        columns[key]["paid_expenses"] += abs(amt)

            # Build sorted column list with running balance
            sorted_dates = sorted(columns.keys())
            column_list = []
            # Get starting balance from accounts
            total_account_balance = sum(
                sum(le.amount for le in db.fetch_ledger_items(acc.id))
                for acc in accounts
            ) if accounts else 0

            running = total_account_balance
            for d in sorted_dates:
                col = columns[d]
                col["starting_balance"] = round(running, 2)
                safe = col["income"] - col["expenses"]
                col["safe_to_spend"] = round(safe, 2)
                col["ending_balance"] = round(running + safe, 2)
                running = col["ending_balance"]
                column_list.append(col)

            # Find current column: last column <= today, or first column if all are future
            current_column = None
            today_str = today.strftime("%Y-%m-%d")
            for col in column_list:
                if col["income_date"] <= today_str:
                    current_column = col
            # Fall back to first column if all dates are in the future
            if current_column is None and column_list:
                current_column = column_list[0]

            return {
                "upcoming": upcoming,
                "overdue": overdue,
                "current_column": current_column,
                "columns": column_list,
                "total_unpaid": len([ei for ei in extrap_items if ei.ledger_entry_id is None and ei.income_date]),
                "total_paid": len([ei for ei in extrap_items if ei.ledger_entry_id is not None]),
                "account_count": len(accounts),
                "budget_item_count": len(budget_items),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Calendar/Extrapolation Endpoints
    # ========================================================================

    @app.get("/schedule/{profile_id}")
    async def get_schedule(profile_id: int):
        try:
            db = Database()
            service = CalendarService(db)
            schedule = service.get_schedule(profile_id)
            return schedule
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/extrapolate/{profile_id}")
    async def run_extrapolation(profile_id: int, request: ExtrapolateRequest):
        try:
            db = Database()
            service = CalendarService(db)
            
            start_date = date.fromisoformat(request.start_date) if request.start_date else None
            end_date = date.fromisoformat(request.end_date) if request.end_date else None
            
            result = service.run_extrapolation(profile_id, start_date, end_date)
            return {"success": True, "count": result["count"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/extrapolate/updateitem/{item_id}")
    async def update_extrapolation_item(item_id: int, update: ExtrapolationItemUpdate):
        try:
            db = Database()
            service = CalendarService(db)
            updated_item = service.update_extrapolation_item(
                item_id=item_id,
                amount=update.amount,
                due_date=update.date
            )
            return {
                "id": updated_item.id,
                "amount": updated_item.amount,
                "date": updated_item.due_date.isoformat() if hasattr(updated_item.due_date, 'isoformat') else str(updated_item.due_date),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/budget/markpaid/{profile_id}")
    async def mark_item_paid(profile_id: int, request: MarkPaidRequest):
        try:
            db = Database()
            service = LedgerService(db)
            
            ledger_entry = service.mark_extrapolation_item_paid(
                extrapolation_item_id=request.extrapolationItemId,
                account_id=request.accountId
            )
            
            return {"success": True, "ledger_entry": {"id": ledger_entry.id}}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/oneoff")
    async def add_one_off(profile_id: int, request: OneOffRequest):
        try:
            db = Database()
            service = CalendarService(db)
            
            result = service.add_one_off_item(
                profile_id=profile_id,
                name=request.name,
                amount=request.amount,
                item_type=request.type,
                income_date=request.incomeDate if request.incomeDate != 'none' else None,
                account_id=request.account,
                is_paid=request.addingOneOffExpensePaid
            )
            
            return {"success": True, **result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/computesavings")
    async def compute_savings(profile_id: int, request: ComputeSavingsRequest):
        try:
            db = Database()
            service = CalendarService(db)
            
            savings = service.compute_savings(profile_id, request.spendingBuffer)
            return {"addedEntries": savings}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/savecomputedsavings")
    async def save_computed_savings(profile_id: int, request: SaveComputedSavingsRequest):
        try:
            db = Database()
            service = CalendarService(db)
            
            entries = [{"date": e.date, "amount": e.amount} for e in request.addedEntries]
            count = service.save_computed_savings(profile_id, entries)
            
            return {"success": True, "count": count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/move_item")
    async def move_item(profile_id: int, request: MoveItemRequest):
        try:
            db = Database()
            count = db.move_extrapolation_items(
                profile_id,
                request.budget_item_id,
                request.from_income_date,
                request.to_income_date,
            )
            return {"success": True, "count": count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/split_item")
    async def split_item(profile_id: int, request: SplitItemRequest):
        try:
            db = Database()
            result = db.split_extrapolation_item(
                request.extrapolation_item_id,
                request.keep_amount,
                request.remainder_income_date,
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/fixunscheduled")
    async def fix_unscheduled(profile_id: int, items: List[FixUnscheduledItem]):
        try:
            db = Database()
            service = CalendarService(db)
            
            unscheduled = [{"id": item.id, "income_date": item.income_date} for item in items]
            count = service.fix_unscheduled_items(unscheduled)
            
            return {"success": True, "count": count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/calendar/{profile_id}/downloadspreadsheet")
    async def download_spreadsheet(profile_id: int, request: DownloadSpreadsheetRequest):
        try:
            db = Database()
            service = CalendarService(db)
            
            # Generate spreadsheet (no file_path argument)
            result = service.download_spreadsheet(profile_id)
            
            # Return the generated file path
            return {"success": True, "filePath": result["path"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/calendar/{profile_id}/downloadspreadsheet")
    async def download_spreadsheet_get(profile_id: int, filename: Optional[str] = None):
        """GET endpoint for downloading ODS spreadsheet - works in browsers."""
        try:
            db = Database()
            service = CalendarService(db)
            
            # Service creates the ODS file directly (no file_path param)
            result = service.download_spreadsheet(profile_id)
            
            # Get the generated file path
            file_path = result["path"]
            download_filename = filename or f'budget_schedule_{profile_id}.ods'
            
            return FileResponse(
                file_path,
                media_type='application/vnd.oasis.opendocument.spreadsheet',
                filename=download_filename,
                headers={
                    "Content-Disposition": f"attachment; filename={download_filename}"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Debt Endpoints
    # ========================================================================

    @app.get("/debts/{profile_id}")
    async def get_debts(profile_id: int):
        try:
            db = Database()
            service = DebtService(db)
            debts = service.get_debts(profile_id)
            return [
                {
                    "id": d.id,
                    "name": d.name,
                    "total_amount": float(d.total_amount),
                    "remaining_amount": float(d.remaining_amount),
                    "min_payment": float(d.min_payment),
                    "interest_rate": float(d.interest_rate),
                    "created_at": d.created_at.isoformat() if hasattr(d.created_at, 'isoformat') else None,
                    "updated_at": d.updated_at.isoformat() if hasattr(d.updated_at, 'isoformat') else None,
                }
                for d in debts
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/debts/{profile_id}")
    async def create_debt(profile_id: int, debt: DebtCreate):
        try:
            db = Database()
            service = DebtService(db)
            new_debt = service.create_debt(
                profile_id=profile_id,
                name=debt.name,
                total_amount=debt.total_amount,
                remaining_amount=debt.remaining_amount,
                min_payment=debt.min_payment,
                interest_rate=debt.interest_rate
            )
            return {
                "id": new_debt.id,
                "name": new_debt.name,
                "total_amount": float(new_debt.total_amount),
                "remaining_amount": float(new_debt.remaining_amount),
                "min_payment": float(new_debt.min_payment),
                "interest_rate": float(new_debt.interest_rate),
                "created_at": new_debt.created_at.isoformat() if new_debt.created_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/debts/{profile_id}/{debt_id}")
    async def update_debt(profile_id: int, debt_id: int, debt: DebtCreate):
        try:
            db = Database()
            service = DebtService(db)
            updated_debt = service.update_debt(
                debt_id=debt_id,
                name=debt.name,
                total_amount=debt.total_amount,
                remaining_amount=debt.remaining_amount,
                min_payment=debt.min_payment,
                interest_rate=debt.interest_rate
            )
            return {
                "id": updated_debt.id,
                "name": updated_debt.name,
                "total_amount": float(updated_debt.total_amount),
                "remaining_amount": float(updated_debt.remaining_amount),
                "min_payment": float(updated_debt.min_payment),
                "interest_rate": float(updated_debt.interest_rate),
                "updated_at": updated_debt.updated_at.isoformat() if updated_debt.updated_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/debts/{profile_id}/{debt_id}")
    async def delete_debt(profile_id: int, debt_id: int):
        try:
            db = Database()
            service = DebtService(db)
            service.delete_debt(debt_id)
            return {"success": True, "id": debt_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/debts/{profile_id}/compute")
    async def compute_debt_payments(profile_id: int, request: ComputeDebtPaymentsRequest):
        try:
            db = Database()
            service = DebtService(db)
            payments = service.compute_debt_payments(profile_id, request.savings_margin)
            return {"payments": payments}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/debts/{profile_id}/save_payments")
    async def save_debt_payments(profile_id: int, request: SaveDebtPaymentsRequest):
        try:
            db = Database()
            service = DebtService(db)
            payments = [
                {
                    "debt_id": p.debt_id,
                    "debt_name": p.debt_name,
                    "amount": p.amount,
                    "income_date": p.income_date,
                }
                for p in request.payments
            ]
            count = service.save_debt_payments(profile_id, payments)
            return {"success": True, "count": count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # AI Analysis Endpoints
    # ========================================================================

    @app.get("/ai/config")
    async def get_ai_config():
        try:
            db = Database()
            service = AIService(db)
            return service.get_config()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/ai/config")
    async def update_ai_config(config: AIConfigUpdate):
        try:
            db = Database()
            service = AIService(db)
            service.save_config(config.server_url, config.model, config.enabled)
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/ai/analyze/{profile_id}")
    async def analyze_budget(profile_id: int):
        try:
            db = Database()
            service = AIService(db)
            result = service.analyze(profile_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Reconciliation Endpoints
    # ========================================================================

    @app.post("/reconcile/{profile_id}/parse")
    async def reconcile_parse(profile_id: int, request: ReconcileParseRequest):
        """Parse a bank CSV and return structured transactions + detected columns."""
        try:
            db = Database()
            service = ReconciliationService(db)
            result = service.parse_csv(
                csv_content=request.csv_content,
                date_col=request.date_col,
                amount_col=request.amount_col,
                desc_col=request.desc_col,
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/reconcile/{profile_id}/match")
    async def reconcile_match(profile_id: int, request: ReconcileMatchRequest):
        """Match parsed transactions against unpaid extrapolation items."""
        try:
            db = Database()
            service = ReconciliationService(db)
            results = service.match_transactions(
                profile_id=profile_id,
                transactions=request.transactions,
                account_id=request.account_id,
                date_tolerance_days=request.date_tolerance_days,
                amount_tolerance_pct=request.amount_tolerance_pct,
            )
            return {"matches": results, "count": len(results)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/reconcile/{profile_id}/import")
    async def reconcile_import(profile_id: int, request: ReconcileImportRequest):
        """Import confirmed reconciliation matches as ledger entries."""
        try:
            db = Database()
            service = ReconciliationService(db)
            confirmed = [
                {
                    "transaction": item.transaction,
                    "extrapolation_item_id": item.extrapolation_item_id,
                    "amount_override": item.amount_override,
                }
                for item in request.confirmed
            ]
            result = service.import_confirmed(
                profile_id=profile_id,
                account_id=request.account_id,
                confirmed=confirmed,
            )
            return {"success": True, **result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Profile Theme Endpoint
    # ========================================================================

    @app.put("/profiles/{profile_id}/theme")
    async def update_profile_theme(profile_id: int, request: ThemeUpdate):
        try:
            db = Database()
            db.update_profile_theme(profile_id, request.theme)
            return {"success": True, "theme": request.theme}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Settings Endpoints
    # ========================================================================

    @app.get("/settings/{key}")
    async def get_setting(key: str):
        try:
            db = Database()
            value = db.get_setting(key)
            if value is None:
                raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
            return {"key": key, "value": value}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/settings/{key}")
    async def set_setting(key: str, request: SettingUpdate):
        try:
            db = Database()
            db.set_setting(key, request.value)
            return {"success": True, "key": key, "value": request.value}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Extrapolation CRUD Endpoints
    # ========================================================================

    @app.get("/extrapolation/{profile_id}")
    async def get_extrapolation_items(profile_id: int):
        try:
            db = Database()
            items = db.fetch_extrapolation_items(profile_id)
            budget_items = db.fetch_budget_items(profile_id)
            budget_map = {bi.id: bi for bi in budget_items}
            result = []
            for ei in items:
                due = ei.due_date
                due_str = due.isoformat() if hasattr(due, 'isoformat') else str(due) if due else None
                inc = ei.income_date
                inc_str = inc.isoformat() if hasattr(inc, 'isoformat') else str(inc) if inc else None
                display_name = ei.name
                if not display_name and ei.budget_item_id and ei.budget_item_id in budget_map:
                    display_name = budget_map[ei.budget_item_id].name
                result.append({
                    "id": ei.id,
                    "due_date": due_str,
                    "amount": float(ei.amount) if ei.amount else 0.0,
                    "income_date": inc_str,
                    "budget_item_id": ei.budget_item_id,
                    "ledger_entry_id": ei.ledger_entry_id,
                    "category": ei.category,
                    "name": display_name,
                })
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/extrapolation/{profile_id}")
    async def clear_extrapolation_items(profile_id: int):
        try:
            db = Database()
            db.clear_extrapolation_items(profile_id)
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/extrapolation/{profile_id}/unpaid")
    async def clear_unpaid_extrapolation_items(profile_id: int):
        try:
            db = Database()
            db.clear_unpaid_extrapolation_items(profile_id)
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/extrapolation/{profile_id}/item")
    async def create_extrapolation_item(profile_id: int, item: ExtrapolationItemCreate):
        try:
            db = Database()
            new_item = db.create_extrapolation_item(
                profileId=profile_id,
                date=item.due_date,
                amount=item.amount,
                income_date=item.income_date,
                budget_item_id=item.budget_item_id,
                category=item.category,
                name=item.name,
            )
            return {
                "id": new_item.id,
                "due_date": str(new_item.due_date),
                "amount": float(new_item.amount),
                "income_date": str(new_item.income_date) if new_item.income_date else None,
                "budget_item_id": new_item.budget_item_id,
                "category": new_item.category,
                "name": new_item.name,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/extrapolation/item/{item_id}/income_date")
    async def update_extrapolation_income_date(item_id: int, request: ExtrapolationIncomeDateUpdate):
        try:
            db = Database()
            db.update_extrapolation_item_income_date(item_id, request.income_date)
            return {"success": True, "id": item_id, "income_date": request.income_date}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/extrapolation/item/{item_id}/ledger_id")
    async def update_extrapolation_ledger_id(item_id: int, request: ExtrapolationLedgerIdUpdate):
        try:
            db = Database()
            db.update_extrapolation_item_ledger_id(item_id, request.ledger_entry_id)
            return {"success": True, "id": item_id, "ledger_entry_id": request.ledger_entry_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Ledger Single Entry Endpoint
    # ========================================================================

    @app.get("/ledger/entry/{ledger_item_id}")
    async def get_ledger_entry(ledger_item_id: int):
        try:
            db = Database()
            entry = db.get_ledger_entry(ledger_item_id)
            if not entry:
                raise HTTPException(status_code=404, detail=f"Ledger entry {ledger_item_id} not found")
            return serialize_ledger_entry(entry)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Export / Import Endpoints
    # ========================================================================

    @app.get("/profile/{profile_id}/export")
    async def export_profile(profile_id: int):
        try:
            db = Database()
            profile = db.get_profile_by_id(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

            accounts = db.fetch_accounts(profile_id)
            budget_groups = db.fetch_budget_groups(profile_id)
            budget_items = db.fetch_budget_items(profile_id)
            debts = db.fetch_debts(profile_id)
            extrapolation_items = db.fetch_extrapolation_items(profile_id)

            # Build lookup maps for name resolution
            group_map = {g.id: g.name for g in budget_groups}
            budget_item_map = {bi.id: bi.name for bi in budget_items}
            debt_map = {d.id: d.name for d in debts}

            def date_to_iso(val):
                if val is None:
                    return None
                if hasattr(val, 'isoformat'):
                    return val.isoformat()
                return str(val)

            # Serialize accounts with ledger entries
            exported_accounts = []
            for acc in accounts:
                ledger_entries = db.fetch_ledger_items(acc.id)
                exported_accounts.append({
                    "name": acc.name,
                    "account_type": acc.account_type,
                    "ledger_entries": [
                        {
                            "name": le.name,
                            "paid_date": date_to_iso(le.paid_date),
                            "income_date": date_to_iso(le.income_date),
                            "type": le.type,
                            "amount": float(le.amount) if le.amount else 0.0,
                        }
                        for le in ledger_entries
                    ],
                })

            # Serialize budget groups
            exported_groups = [{"name": g.name} for g in budget_groups]

            # Serialize budget items with periods, using names for references
            exported_budget_items = []
            for bi in budget_items:
                periods = []
                if hasattr(bi, 'periods') and bi.periods:
                    periods = [
                        {
                            "type": p.type,
                            "value": p.value,
                            "business_day": p.business_day if hasattr(p, 'business_day') else None,
                        }
                        for p in bi.periods
                    ]
                exported_budget_items.append({
                    "name": bi.name,
                    "type": bi.type,
                    "amount": float(bi.amount) if bi.amount else 0.0,
                    "start_date": date_to_iso(bi.start_date),
                    "end_date": date_to_iso(bi.end_date),
                    "budget_group_name": group_map.get(bi.budget_group_id) or (bi.budget_group_id if isinstance(bi.budget_group_id, str) else None),
                    "debt_name": debt_map.get(bi.debt_id) if hasattr(bi, 'debt_id') and bi.debt_id else None,
                    "periods": periods,
                })

            # Serialize debts
            exported_debts = [
                {
                    "name": d.name,
                    "total_amount": float(d.total_amount),
                    "remaining_amount": float(d.remaining_amount),
                    "min_payment": float(d.min_payment),
                    "interest_rate": float(d.interest_rate),
                }
                for d in debts
            ]

            # Serialize extrapolation items, using budget item name for reference
            exported_extrap = []
            for ei in extrapolation_items:
                exported_extrap.append({
                    "due_date": date_to_iso(ei.due_date),
                    "amount": float(ei.amount) if ei.amount else 0.0,
                    "income_date": date_to_iso(ei.income_date),
                    "budget_item_name": budget_item_map.get(ei.budget_item_id),
                    "ledger_entry_linked": ei.ledger_entry_id is not None,
                    "category": ei.category,
                    "name": ei.name,
                })

            return {
                "version": 1,
                "exported_at": datetime.now().isoformat(),
                "profile": {
                    "name": profile.name,
                    "theme": profile.theme or "dark",
                    "hidden_through": date_to_iso(profile.hidden_through),
                },
                "accounts": exported_accounts,
                "budget_groups": exported_groups,
                "budget_items": exported_budget_items,
                "debts": exported_debts,
                "extrapolation_items": exported_extrap,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/profile/import")
    async def import_profile(request: ImportRequest):
        try:
            db = Database()

            # 1. Create the profile
            profile = db.create_profile(request.profile.name)

            # 2. Update theme if specified
            if request.profile.theme:
                db.update_profile_theme(profile.id, request.profile.theme)

            # 3. Update hidden_through if specified
            if request.profile.hidden_through:
                db.update_profile_hidden_through(profile.id, request.profile.hidden_through)

            # 4. Create budget groups, build name->id map
            group_name_to_id = {}
            for g in request.budget_groups:
                new_group = db.create_budget_group(profile.id, g.name)
                group_name_to_id[g.name] = new_group.id

            # 5. Create debts, build name->id map
            debt_name_to_id = {}
            for d in request.debts:
                new_debt = db.create_debt(
                    profile.id,
                    d.name,
                    d.total_amount,
                    d.remaining_amount,
                    d.min_payment,
                    d.interest_rate,
                )
                debt_name_to_id[d.name] = new_debt.id

            # 6. Create accounts and their ledger entries
            for acc in request.accounts:
                new_account = db.create_account(profile.id, acc.name, acc.account_type, 0.0)
                for le in acc.ledger_entries:
                    # Insert ledger entries directly to handle string dates
                    cursor = db.db.cursor()
                    now = datetime.now()
                    cursor.execute(
                        """INSERT INTO ledger_entry
                           (name, paid_date, income_date, type, amount, account_id, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (le.name, le.paid_date, le.income_date, le.type,
                         le.amount, new_account.id, now, now),
                    )
                    db.db.commit()

            # 7. Create budget items with resolved group/debt IDs
            budget_item_name_to_id = {}
            for bi in request.budget_items:
                group_id = group_name_to_id.get(bi.budget_group_name) if bi.budget_group_name else None
                debt_id = debt_name_to_id.get(bi.debt_name) if bi.debt_name else None
                from database.budget_item_period import BudgetItemPeriod as BIPeriod
                periods = [
                    BIPeriod(p.type, p.value, p.business_day, None)
                    for p in bi.periods
                ]
                new_item = db.create_budget_item(
                    profileId=profile.id,
                    name=bi.name,
                    type=bi.type,
                    amount=bi.amount,
                    group=group_id,
                    start_date=bi.start_date,
                    end_date=bi.end_date,
                    periods=periods,
                    debt_id=debt_id,
                )
                budget_item_name_to_id[bi.name] = new_item.id

            # 8. Create extrapolation items, resolving budget item by name
            for ei in request.extrapolation_items:
                budget_item_id = budget_item_name_to_id.get(ei.budget_item_name) if ei.budget_item_name else None
                db.create_extrapolation_item(
                    profileId=profile.id,
                    date=ei.due_date,
                    amount=ei.amount,
                    income_date=ei.income_date,
                    budget_item_id=budget_item_id,
                    category=ei.category,
                    name=ei.name,
                )

            return {
                "success": True,
                "profile_id": profile.id,
                "profile_name": profile.name,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

    # ========================================================================
    # Static Files (Frontend)
    # ========================================================================

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
