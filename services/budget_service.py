"""
Budget Service - Handles all budget-related business logic.
Used by both Qt app and API.
"""

from typing import List
from database.database import Database
from database.budget_item import BudgetItem
from database.budget_group import BudgetGroup
from database.budget_item_period import BudgetItemPeriod


class BudgetService:
    """Service for budget items and groups operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # Budget Items
    
    def get_budget_items(self, profile_id: int) -> list[BudgetItem]:
        """Get all budget items for a profile."""
        return self.db.fetch_budget_items(profile_id)
    
    def get_budget_item_by_id(self, budget_item_id: int, profile_id: int) -> BudgetItem:
        """Get a specific budget item by ID."""
        items = self.db.fetch_budget_items(profile_id)
        for item in items:
            if item.id == budget_item_id:
                return item
        return None
    
    def create_budget_item(
        self,
        profile_id: int,
        name: str,
        item_type: str,
        amount: float,
        group_id: int,
        start_date: str,
        end_date: str,
        periods: List[dict],
        debt_id: int = None,
    ) -> BudgetItem:
        """Create a new budget item with periods."""
        # Convert period dicts to BudgetItemPeriod objects
        period_objects = []
        for period in periods:
            period_obj = BudgetItemPeriod(
                period.get('type'),
                period.get('value'),
                period.get('business_day'),
                None  # budget_item_id set later
            )
            period_objects.append(period_obj)

        return self.db.create_budget_item(
            profileId=profile_id,
            name=name,
            type=item_type,
            amount=amount,
            group=group_id,
            start_date=start_date,
            end_date=end_date,
            periods=period_objects,
            debt_id=debt_id,
        )
    
    def update_budget_item(
        self,
        budget_item_id: int,
        name: str,
        item_type: str,
        amount: float,
        group_id: int,
        start_date: str,
        end_date: str,
        periods: List[dict],
        debt_id: int = None,
    ) -> BudgetItem:
        """Update an existing budget item."""
        # Convert period dicts to BudgetItemPeriod objects
        period_objects = []
        for period in periods:
            period_obj = BudgetItemPeriod(
                period.get('type'),
                period.get('value'),
                period.get('business_day'),
                budget_item_id
            )
            period_objects.append(period_obj)

        return self.db.update_budget_item(
            budget_item_id=budget_item_id,
            name=name,
            type=item_type,
            amount=amount,
            group=group_id,
            start_date=start_date,
            end_date=end_date,
            periods=period_objects,
            debt_id=debt_id,
        )
    
    def delete_budget_item(self, budget_item_id: int) -> None:
        """Delete a budget item."""
        self.db.delete_budget_item(budget_item_id)
    
    # Budget Groups
    
    def get_budget_groups(self, profile_id: int) -> list[BudgetGroup]:
        """Get all budget groups for a profile."""
        return self.db.fetch_budget_groups(profile_id)
    
    def create_budget_group(self, profile_id: int, name: str) -> BudgetGroup:
        """Create a new budget group."""
        return self.db.create_budget_group(profile_id, name)
    
    def delete_budget_group(self, group_id: int) -> None:
        """Delete a budget group."""
        self.db.delete_budget_group(group_id)
