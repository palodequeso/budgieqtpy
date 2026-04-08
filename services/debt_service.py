"""
Debt Service - Handles all debt-related business logic.
Used by both Qt app and API.
"""

from typing import List, Optional
from database.database import Database
from database.debt import Debt


class DebtService:
    """Service for debt payoff operations."""

    def __init__(self, db: Database):
        self.db = db

    def get_debts(self, profile_id: int) -> list[Debt]:
        """Get all debts for a profile."""
        return self.db.fetch_debts(profile_id)

    def create_debt(
        self,
        profile_id: int,
        name: str,
        total_amount: float,
        remaining_amount: float,
        min_payment: float,
        interest_rate: float
    ) -> Debt:
        """Create a new debt."""
        return self.db.create_debt(
            profileId=profile_id,
            name=name,
            total_amount=total_amount,
            remaining_amount=remaining_amount,
            min_payment=min_payment,
            interest_rate=interest_rate
        )

    def update_debt(
        self,
        debt_id: int,
        name: str,
        total_amount: float,
        remaining_amount: float,
        min_payment: float,
        interest_rate: float
    ) -> Debt:
        """Update an existing debt."""
        return self.db.update_debt(
            debt_id=debt_id,
            name=name,
            total_amount=total_amount,
            remaining_amount=remaining_amount,
            min_payment=min_payment,
            interest_rate=interest_rate
        )

    def delete_debt(self, debt_id: int) -> None:
        """Delete a debt."""
        self.db.delete_debt(debt_id)

    def compute_debt_payments(
        self,
        profile_id: int,
        savings_margin: float
    ) -> list[dict]:
        """
        Compute debt payment plan from the saved schedule's surplus.

        Uses the actual saved schedule (including savings, one-offs, etc.)
        to find real surplus per column. Allocates toward debts using the
        avalanche method (highest interest first). Stops once all debts
        are fully covered.

        Returns list of {debt_id, debt_name, amount, income_date} entries.
        """
        from shedule.schedule import Schedule

        # Get debts sorted by interest rate descending (avalanche method)
        debts = self.db.fetch_debts(profile_id)
        debts = [d for d in debts if d.remaining_amount > 0]
        debts.sort(key=lambda d: d.interest_rate, reverse=True)

        if not debts:
            return []

        # Use the actual saved schedule (includes savings, one-offs, etc.)
        schedule = Schedule()
        schedule.fetch_schedule(self.db, profile_id)
        schedule.build_schedule()

        if not schedule.sorted_income_dates:
            return []

        payments = []
        debt_remaining = {d.id: d.remaining_amount for d in debts}
        total_debt = sum(d.remaining_amount for d in debts)

        for income_date in schedule.sorted_income_dates:
            # Stop if all debts are paid off
            if total_debt <= 0:
                break

            date_key = income_date.strftime("%Y-%m-%d")
            column = schedule.columns.get(date_key)
            if not column:
                continue

            # Use the column's actual total (carry + income + expenses)
            # Surplus = column total - carry = net of this column's income + expenses
            col_net = float(column.income_total()) + float(column.expenses_total())
            available = col_net - savings_margin
            if available <= 0:
                continue

            # Allocate available funds to debts (avalanche: highest interest first)
            for debt in debts:
                remaining = debt_remaining[debt.id]
                if remaining <= 0:
                    continue
                if available <= 0:
                    break

                payment = min(available, remaining)
                if payment <= 0:
                    continue

                payments.append({
                    "debt_id": debt.id,
                    "debt_name": debt.name,
                    "amount": round(payment, 2),
                    "income_date": income_date.isoformat(),
                })

                debt_remaining[debt.id] -= payment
                available -= payment
                total_debt -= payment

        return payments

    def save_debt_payments(
        self,
        profile_id: int,
        payments: list[dict]
    ) -> int:
        """
        Save computed debt payments as extrapolation items with category='debt_payment'.
        Returns the number of items created.
        """
        count = 0
        for payment in payments:
            self.db.create_extrapolation_item(
                profileId=profile_id,
                date=payment['income_date'],
                amount=-payment['amount'],  # Negative for expense
                income_date=payment['income_date'],
                budget_item_id=None,
                category='debt_payment',
                name=payment.get('debt_name'),
            )
            count += 1

        return count
