"""
Fast-API Server
"""

import os
from typing import Optional, List
from datetime import date
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
    CalendarService
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
    value: int
    business_day: Optional[str] = None

class BudgetItemCreate(BaseModel):
    name: str
    amount: float
    type: str
    budget_group_id: int
    start_date: str
    end_date: str
    periods: List[BudgetPeriod]

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

class DownloadSpreadsheetRequest(BaseModel):
    filePath: Optional[str] = None

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
            return {
                "id": new_profile.id,
                "name": new_profile.name,
                "created_at": new_profile.created_at.isoformat() if new_profile.created_at else None,
                "updated_at": new_profile.updated_at.isoformat() if new_profile.updated_at else None,
            }
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
                periods=periods
            )
            return {
                "id": new_item.id,
                "name": new_item.name,
                "type": new_item.type,
                "amount": new_item.amount,
                "budget_group_id": new_item.budget_group_id,
                "start_date": new_item.start_date.isoformat() if new_item.start_date else None,
                "end_date": new_item.end_date.isoformat() if new_item.end_date else None,
                "created_at": new_item.created_at.isoformat() if new_item.created_at else None,
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
                periods=periods
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
            return {
                "id": new_group.id,
                "name": new_group.name,
                "created_at": new_group.created_at.isoformat() if new_group.created_at else None,
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
    # Static Files (Frontend)
    # ========================================================================

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
