"""
Calendar Service - Handles all calendar/extrapolation/scheduling business logic.
Used by both Qt app and API.
"""

from datetime import date, timedelta
from typing import List, Optional
from database.database import Database
from database.extrapolation_item import ExtrapolationItem
from scheduler.default_knapsack import DefaultKnapsack
from shedule.schedule import Schedule
from shedule.schedule_writer import ScheduleWriter


class CalendarService:
    """Service for calendar, extrapolation, and scheduling operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_schedule(self, profile_id: int):
        """Get the schedule for a profile."""
        from api.schedule import ScheduleAPI
        schedule_api = ScheduleAPI(self.db)
        return schedule_api.get_by_profile_id(profile_id)
    
    def run_extrapolation(
        self,
        profile_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """
        Run the extrapolation/scheduling algorithm.
        This is the core scheduling logic used by both apps.
        """
        knapsack = DefaultKnapsack(self.db, profile_id)
        
        # Set date range
        start = start_date or date.today()
        end = end_date or (date.today() + timedelta(days=365))
        
        knapsack.start_date = start
        knapsack.end_date = end
        
        # Clear only unpaid extrapolation items (preserve paid ones with ledger entries)
        self.db.clear_unpaid_extrapolation_items(profile_id)
        
        # Build schedule
        knapsack.schedule = Schedule()
        knapsack.build_input_date_columns()
        knapsack.build_unscheduled_schedule_entries()
        
        # Schedule expenses (two passes, matching DefaultKnapsack.run)
        unscheduled = knapsack.schedule_expense_entries_pass(
            knapsack.unscheduled_schedule_entries
        )

        # Second pass: push expenses up to find spots if possible
        knapsack.push_expenses_up = True
        unscheduled = knapsack.schedule_expense_entries_pass(unscheduled)

        # Save extrapolation items
        count = 0
        for date_key, column in knapsack.schedule.columns.items():
            for income in column.incomes:
                self.db.create_extrapolation_item(
                    profileId=profile_id,
                    date=income.due_date,
                    amount=income.amount,
                    income_date=income.income_date,
                    budget_item_id=income.budget_item_id
                )
                count += 1
            for expense in column.expenses:
                self.db.create_extrapolation_item(
                    profileId=profile_id,
                    date=expense.due_date,
                    amount=expense.amount,
                    income_date=expense.income_date,
                    budget_item_id=expense.budget_item_id
                )
                count += 1

        # Save unscheduled entries with income_date=None so they persist in the DB
        for entry in unscheduled:
            self.db.create_extrapolation_item(
                profileId=profile_id,
                date=entry.due_date,
                amount=entry.amount,
                income_date=None,
                budget_item_id=entry.budget_item_id
            )
            count += 1
        
        # Rebuild schedule from saved extrapolation items to ensure proper data structure
        final_schedule = Schedule()
        final_schedule.fetch_schedule(self.db, profile_id)
        final_schedule.build_schedule()
        
        return {
            "success": True,
            "count": count,
            "unscheduled_count": len(unscheduled),
            "schedule": final_schedule
        }
    
    def get_extrapolation_items(self, profile_id: int) -> list[ExtrapolationItem]:
        """Get all extrapolation items for a profile."""
        return self.db.fetch_extrapolation_items(profile_id)
    
    def update_extrapolation_item(
        self,
        item_id: int,
        amount: Optional[float] = None,
        due_date: Optional[str] = None
    ) -> ExtrapolationItem:
        """Update an extrapolation item's amount and/or date."""
        return self.db.update_extrapolation_item(
            item_id=item_id,
            amount=amount,
            date=due_date
        )
    
    def add_one_off_item(
        self,
        profile_id: int,
        name: str,
        amount: float,
        item_type: str,
        income_date: Optional[str] = None,
        account_id: Optional[int] = None,
        is_paid: bool = False
    ) -> dict:
        """
        Add a one-off expense or income.
        If is_paid=True, creates a ledger entry.
        Otherwise, creates an extrapolation item.
        """
        if is_paid and account_id:
            # Create ledger entry for paid item
            from .ledger_service import LedgerService
            ledger_service = LedgerService(self.db)
            
            ledger_entry = ledger_service.create_ledger_entry(
                account_id=account_id,
                amount=amount,
                paid_date=date.today().isoformat(),
                income_date=income_date or date.today().isoformat(),
                name=name,
                entry_type=item_type
            )
            
            return {"type": "ledger", "entry": ledger_entry}
        else:
            # Create extrapolation item for unpaid/future item
            extrap_item = self.db.create_extrapolation_item(
                profileId=profile_id,
                date=date.today().isoformat(),
                amount=amount,
                income_date=income_date,
                budget_item_id=None,
                category='one_off'
            )
            
            return {"type": "extrapolation", "item": extrap_item}
    
    def compute_savings(
        self,
        profile_id: int,
        spending_buffer: float
    ) -> List[dict]:
        """
        Compute potential savings by analyzing schedule surplus.
        Returns list of opportunities to save money.
        """
        knapsack = DefaultKnapsack(self.db, profile_id)
        
        # Compute savings opportunities
        savings_items = knapsack.compute_savings()
        
        # Format for response and apply spending buffer
        added_entries = []
        for item in savings_items:
            if hasattr(item, 'income_date') and hasattr(item, 'amount'):
                if item.amount > spending_buffer:
                    added_entries.append({
                        "date": item.income_date.isoformat() if hasattr(item.income_date, 'isoformat') else str(item.income_date),
                        "amount": item.amount - spending_buffer
                    })
        
        return added_entries
    
    def save_computed_savings(
        self,
        profile_id: int,
        savings_entries: List[dict]
    ) -> int:
        """
        Save computed savings as extrapolation items (transfers to savings).
        Returns the number of items created.
        """
        count = 0
        for entry in savings_entries:
            self.db.create_extrapolation_item(
                profileId=profile_id,
                date=entry['date'],
                amount=-entry['amount'],  # Negative for transfer out
                income_date=entry['date'],
                budget_item_id=None,
                category='savings'
            )
            count += 1
        
        return count
    
    def fix_unscheduled_items(
        self,
        unscheduled_items: List[dict]
    ) -> int:
        """
        Fix unscheduled items by assigning them income dates.
        Returns the number of items fixed.
        """
        count = 0
        for item in unscheduled_items:
            self.db.update_extrapolation_item_income_date(
                item_id=item['id'],
                income_date=item['income_date']
            )
            count += 1
        
        return count
    
    def download_spreadsheet(
        self,
        profile_id: int
    ) -> dict:
        """
        Generate and download schedule spreadsheet.
        Returns path to the generated ODS file.
        """
        # Build schedule
        schedule = Schedule()
        schedule.fetch_schedule(self.db, profile_id)
        schedule.build_schedule()
        
        # Write spreadsheet - creates file in schedule-spreadsheets/ folder
        writer = ScheduleWriter(schedule)
        writer.write_spreadsheet()
        
        # Get the most recent file created in schedule-spreadsheets/
        import os
        import glob
        spreadsheet_dir = "schedule-spreadsheets"
        files = glob.glob(os.path.join(spreadsheet_dir, f"schedule.{profile_id}.*.ods"))
        if not files:
            raise FileNotFoundError(f"No spreadsheet generated for profile {profile_id}")
        
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        return {"type": "file", "path": latest_file}
