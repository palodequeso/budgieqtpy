"""
Integration tests for the Budgie FastAPI backend.

Each test gets a fresh SQLite database via the `app` fixture (conftest.py).
Run with: venv/bin/python -m pytest tests/test_integration.py -v
"""

import sqlite3
import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _query_extrapolation_items(db_path, profile_id):
    """Return extrapolation items for a profile as plain dicts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, due_date, amount, income_date, ledger_entry_id, category
           FROM extrapolation_item WHERE profile_id = ?""",
        (profile_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "due_date": r[1],
            "amount": float(r[2]),
            "income_date": r[3],
            "ledger_entry_id": r[4],
            "category": r[5],
        }
        for r in rows
    ]


def _create_profile(client, name="Test"):
    r = client.post("/profiles", json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


def _create_account(client, pid, name="Checking", balance=0):
    r = client.post(f"/accounts/{pid}", json={"name": name, "type": "Checking", "balance": balance})
    assert r.status_code == 200, r.text
    return r.json()


def _create_group(client, pid, name="General"):
    r = client.post(f"/budget/group/{pid}", json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


def _create_budget_item(client, pid, gid, name, amount, item_type, periods, start, end):
    r = client.post(f"/budget/{pid}", json={
        "name": name,
        "amount": amount,
        "type": item_type,
        "budget_group_id": gid,
        "start_date": start,
        "end_date": end,
        "periods": periods,
    })
    assert r.status_code == 200, r.text
    return r.json()


def _extrapolate(client, pid, start, end):
    r = client.post(f"/extrapolate/{pid}", json={
        "profileID": pid,
        "start_date": start,
        "end_date": end,
    })
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Scenario 1: Profile CRUD (smoke test)
# ---------------------------------------------------------------------------

def test_profile_crud(app):
    client, _ = app

    r = client.post("/profiles", json={"name": "Alice"})
    assert r.status_code == 200
    created = r.json()
    assert "id" in created
    assert created["name"] == "Alice"

    r2 = client.get("/profiles")
    assert r2.status_code == 200
    profiles = r2.json()
    assert any(p["id"] == created["id"] and p["name"] == "Alice" for p in profiles)


# ---------------------------------------------------------------------------
# Scenario 2: Account balance
# ---------------------------------------------------------------------------

def test_account_balance(app):
    client, _ = app

    pid = _create_profile(client, "Bob")["id"]
    aid = _create_account(client, pid)["id"]

    today = date.today().isoformat()
    r = client.post(f"/ledger/{pid}", json={
        "account_id": aid,
        "amount": 500,
        "date": today,
        "income_date": today,
    })
    assert r.status_code == 200

    profile_data = client.get(f"/profiles/{pid}").json()
    account = next(a for a in profile_data["accounts"] if a["id"] == aid)
    assert account["balance"] == 500.0


# ---------------------------------------------------------------------------
# Scenario 3: Monthly extrapolation — item count
#
# Three income dates (Jan 15, Feb 15, Mar 15) with a monthly $3000 income item.
# start=2025-01-15, end=2025-04-14 → months = ceil(90/30) = 3.
# Expect exactly 3 income extrapolation items (one per column), no expenses.
# ---------------------------------------------------------------------------

def test_monthly_extrapolation_count(app):
    client, db_path = app

    pid = _create_profile(client, "Carol")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )

    result = _extrapolate(client, pid, "2025-01-15", "2025-04-14")
    assert result["success"] is True
    assert result["count"] == 3

    items = _query_extrapolation_items(db_path, pid)
    assert len(items) == 3
    assert all(item["amount"] > 0 for item in items)


# ---------------------------------------------------------------------------
# Scenario 4: Income + expenses — net balance math
#
# $2000 income on 15th, $1000 rent + $100 insurance on 1st.
# Expenses are stored as negative. For the Jan 15 income column the net
# should be 2000 + (−1000) + (−100) = 900.
# ---------------------------------------------------------------------------

def test_income_expense_sign_and_net(app):
    client, db_path = app

    pid = _create_profile(client, "Dave")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=2000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Insurance", amount=100, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-04-14")

    items = _query_extrapolation_items(db_path, pid)
    assert len(items) > 0

    # All expense items must have negative amounts
    expenses = [i for i in items if i["amount"] < 0]
    incomes = [i for i in items if i["amount"] > 0]
    assert len(expenses) > 0, "Expected at least one expense item"
    assert len(incomes) > 0, "Expected at least one income item"

    # Verify net for the Jan 15 income column
    jan15_items = [i for i in items if i["income_date"] == "2025-01-15"]
    assert len(jan15_items) > 0, "No items scheduled to Jan 15 income column"
    net = sum(i["amount"] for i in jan15_items)
    assert net == pytest.approx(900.0), f"Expected net 900 for Jan 15 column, got {net}"


# ---------------------------------------------------------------------------
# Scenario 5: Multiple periods — paid twice a month
#
# Income item with periods "15th" and "Last", extrapolated for 2 months.
# start=2025-01-15, end=2025-03-14 → months = ceil(59/30) = 2.
# Dates: 15th → [Jan 15, Feb 15], Last → [Jan 31, Feb 28] → 4 income items.
# ---------------------------------------------------------------------------

def test_two_periods_per_month(app):
    client, db_path = app

    pid = _create_profile(client, "Eve")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=1500, item_type="Income",
        periods=[
            {"type": "Monthly", "value": "15th", "business_day": ""},
            {"type": "Monthly", "value": "Last", "business_day": ""},
        ],
        start="2025-01-15", end="2025-03-14",
    )

    result = _extrapolate(client, pid, "2025-01-15", "2025-03-14")
    assert result["success"] is True
    assert result["count"] == 4

    items = _query_extrapolation_items(db_path, pid)
    due_dates = sorted(i["due_date"] for i in items)
    assert "2025-01-15" in due_dates
    assert "2025-01-31" in due_dates
    assert "2025-02-15" in due_dates
    assert "2025-02-28" in due_dates


# ---------------------------------------------------------------------------
# Scenario 6: "Last" day of month
#
# Monthly item on "Last", income on 20th as anchor.
# start=2025-02-01, end=2025-04-30 → months = ceil(89/30) = 3.
# Expense due_dates: Feb 28, Mar 31, Apr 30.
# ---------------------------------------------------------------------------

def test_last_day_of_month(app):
    client, db_path = app

    pid = _create_profile(client, "Frank")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    # Income anchor so expenses get scheduled
    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=5000, item_type="Income",
        periods=[{"type": "Monthly", "value": "20th", "business_day": ""}],
        start="2025-02-01", end="2025-04-30",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=300, item_type="Expense",
        periods=[{"type": "Monthly", "value": "Last", "business_day": ""}],
        start="2025-02-01", end="2025-04-30",
    )

    _extrapolate(client, pid, "2025-02-01", "2025-04-30")

    items = _query_extrapolation_items(db_path, pid)
    expense_due_dates = {i["due_date"] for i in items if i["amount"] < 0}

    assert "2025-02-28" in expense_due_dates, f"Expected Feb 28, got {expense_due_dates}"
    assert "2025-03-31" in expense_due_dates, f"Expected Mar 31, got {expense_due_dates}"
    assert "2025-04-30" in expense_due_dates, f"Expected Apr 30, got {expense_due_dates}"


# ---------------------------------------------------------------------------
# Scenario 7: Business day adjustment
#
# Feb 15, 2025 is a Saturday. Monthly income item on "15th" with
# business_day="Previous" should land on Feb 14 (Friday).
# start=2025-01-15, end=2025-02-28 → months = ceil(45/30) = 2.
# Income due_dates: Jan 15 (Wed, no change) and Feb 14 (Fri, adjusted).
# ---------------------------------------------------------------------------

def test_business_day_previous_adjustment(app):
    client, db_path = app

    # Verify our assumption about Feb 15, 2025
    feb15 = date(2025, 2, 15)
    assert feb15.weekday() == 5, "Feb 15 2025 must be Saturday for this test"

    pid = _create_profile(client, "Grace")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": "Previous"}],
        start="2025-01-15", end="2025-02-28",
    )

    result = _extrapolate(client, pid, "2025-01-15", "2025-02-28")
    assert result["count"] == 2

    items = _query_extrapolation_items(db_path, pid)
    due_dates = {i["due_date"] for i in items}

    assert "2025-01-15" in due_dates, f"Expected Jan 15 (unchanged), got {due_dates}"
    assert "2025-02-14" in due_dates, f"Expected Feb 14 (Friday before Sat Feb 15), got {due_dates}"


# ---------------------------------------------------------------------------
# Scenario 8: Mark paid → re-extrapolate preserves paid items
#
# clear_unpaid_extrapolation_items only deletes items without ledger entries.
# After re-extrapolation the paid item should be preserved with its
# ledger_entry_id intact.
# ---------------------------------------------------------------------------

def test_mark_paid_survives_reextrapolation(app):
    client, db_path = app

    pid = _create_profile(client, "Heidi")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-04-14")

    # Pick one item and mark it as paid
    items = _query_extrapolation_items(db_path, pid)
    assert len(items) > 0
    target_id = items[0]["id"]

    r = client.post(f"/budget/markpaid/{pid}", json={
        "extrapolationItemId": target_id,
        "accountId": aid,
    })
    assert r.status_code == 200

    # Verify it has a ledger entry now
    items_after_pay = _query_extrapolation_items(db_path, pid)
    paid_item = next((i for i in items_after_pay if i["id"] == target_id), None)
    assert paid_item is not None
    assert paid_item["ledger_entry_id"] is not None

    # Re-extrapolate — paid item should survive
    _extrapolate(client, pid, "2025-01-15", "2025-04-14")

    items_after_reextrap = _query_extrapolation_items(db_path, pid)
    surviving_paid = next(
        (i for i in items_after_reextrap if i["id"] == target_id), None
    )

    assert surviving_paid is not None, "Paid item was deleted by re-extrapolation"
    assert surviving_paid["ledger_entry_id"] is not None, "Paid item lost its ledger link"


# ---------------------------------------------------------------------------
# Scenario 9: Savings mark-paid → correct account balance
#
# Savings extrapolation items are stored with negative amounts.
# When marking paid against a savings account the ledger entry should
# be positive (abs fix in ledger_service.py).
# ---------------------------------------------------------------------------

def test_savings_markpaid_positive_balance(app):
    client, db_path = app

    pid = _create_profile(client, "Ivan")["id"]
    _create_account(client, pid, name="Checking")
    savings = _create_account(client, pid, name="Savings")
    savings_id = savings["id"]

    today = date.today().isoformat()

    # Directly create a savings extrapolation item via the save_computed_savings endpoint.
    # This stores amount=-500 with category='savings'.
    r = client.post(f"/calendar/{pid}/savecomputedsavings", json={
        "addedEntries": [{"date": today, "amount": 500}],
        "savingsAccount": savings_id,
    })
    assert r.status_code == 200
    assert r.json()["count"] == 1

    # Retrieve the savings extrapolation item from the DB
    items = _query_extrapolation_items(db_path, pid)
    savings_item = next((i for i in items if i["category"] == "savings"), None)
    assert savings_item is not None, "Savings extrapolation item not found"
    assert savings_item["amount"] == pytest.approx(-500.0), (
        "Savings item should be stored as negative (outflow)"
    )

    # Mark it paid against the savings account
    r = client.post(f"/budget/markpaid/{pid}", json={
        "extrapolationItemId": savings_item["id"],
        "accountId": savings_id,
    })
    assert r.status_code == 200, r.text

    # Savings account balance should be POSITIVE (+500), not −500
    profile_data = client.get(f"/profiles/{pid}").json()
    savings_account = next(a for a in profile_data["accounts"] if a["id"] == savings_id)
    assert savings_account["balance"] == pytest.approx(500.0), (
        f"Expected savings balance +500, got {savings_account['balance']} "
        "(check abs(amount) fix in ledger_service.py)"
    )


# ---------------------------------------------------------------------------
# Scenario 10: Partially paid column — mix of paid and unpaid items
#
# Two expenses in one column, mark only one paid.
# Re-extrapolate: the paid item should survive, the unpaid should be
# regenerated, and the schedule should still be valid.
# ---------------------------------------------------------------------------

def test_partially_paid_column(app):
    client, db_path = app

    pid = _create_profile(client, "Partial")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Electric", amount=150, item_type="Expense",
        periods=[{"type": "Monthly", "value": "5th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-03-14")

    items = _query_extrapolation_items(db_path, pid)
    expenses = [i for i in items if i["amount"] < 0]
    assert len(expenses) >= 2, "Need at least 2 expenses for partial pay test"

    # Mark only the first expense as paid
    paid_id = expenses[0]["id"]
    r = client.post(f"/budget/markpaid/{pid}", json={
        "extrapolationItemId": paid_id,
        "accountId": aid,
    })
    assert r.status_code == 200

    # Re-extrapolate
    _extrapolate(client, pid, "2025-01-15", "2025-03-14")

    items_after = _query_extrapolation_items(db_path, pid)

    # Paid item survives
    surviving = next((i for i in items_after if i["id"] == paid_id), None)
    assert surviving is not None, "Paid expense was wiped"
    assert surviving["ledger_entry_id"] is not None

    # Unpaid items still exist (regenerated)
    unpaid = [i for i in items_after if i["ledger_entry_id"] is None and i["amount"] < 0]
    assert len(unpaid) > 0, "Unpaid expenses should be regenerated"


# ---------------------------------------------------------------------------
# Scenario 11: Thin margin — expenses nearly equal income
#
# $2000 income, $1950 in expenses. The scheduler should still place
# all items. Net per column should be $50.
# ---------------------------------------------------------------------------

def test_thin_margin_scheduling(app):
    client, db_path = app

    pid = _create_profile(client, "ThinMargin")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=2000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1200, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Car", amount=500, item_type="Expense",
        periods=[{"type": "Monthly", "value": "10th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Insurance", amount=250, item_type="Expense",
        periods=[{"type": "Monthly", "value": "12th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )

    result = _extrapolate(client, pid, "2025-01-15", "2025-03-14")
    assert result["success"] is True

    items = _query_extrapolation_items(db_path, pid)
    scheduled = [i for i in items if i["income_date"] is not None]
    unscheduled = [i for i in items if i["income_date"] is None]

    # All items should be scheduled — income covers expenses
    assert len(unscheduled) == 0, f"Expected 0 unscheduled, got {len(unscheduled)}"

    # Verify all expenses are scheduled and balance never goes negative
    total_income = sum(i["amount"] for i in scheduled if i["amount"] > 0)
    total_expense = sum(i["amount"] for i in scheduled if i["amount"] < 0)

    # Income should exceed expenses (thin margin, not over budget)
    assert total_income > 0
    assert total_expense < 0
    assert total_income + total_expense > 0, (
        f"Net should be positive: income={total_income}, expense={total_expense}"
    )


# ---------------------------------------------------------------------------
# Scenario 12: Over-budget — expenses exceed income → unscheduled items
#
# $1000 income, $1500 in expenses. Some expenses should be unscheduled.
# ---------------------------------------------------------------------------

def test_over_budget_creates_unscheduled(app):
    """When expenses massively exceed income, some must remain unscheduled."""
    client, db_path = app

    pid = _create_profile(client, "OverBudget")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    # Tiny income, huge expenses — guaranteed unschedulable
    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=500, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=2000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Car", amount=3000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "5th", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )

    result = _extrapolate(client, pid, "2025-01-15", "2025-02-14")
    assert result["success"] is True

    items = _query_extrapolation_items(db_path, pid)
    unscheduled = [i for i in items if i["income_date"] is None]

    # At least one expense should be unscheduled (income $500 can't cover $5000)
    assert len(unscheduled) > 0, (
        "Expected unscheduled items when expenses ($5000) far exceed income ($500)"
    )


# ---------------------------------------------------------------------------
# Scenario 13: Schedule endpoint returns correct structure
#
# Verify GET /schedule/{pid} returns properly nested columns with
# incomes/expenses separated correctly (regression test for the
# lowercase "expense" type case-sensitivity bug).
# ---------------------------------------------------------------------------

def test_schedule_endpoint_structure(app):
    client, db_path = app

    pid = _create_profile(client, "Structure")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-02-14")

    r = client.get(f"/schedule/{pid}")
    assert r.status_code == 200
    schedule = r.json()

    assert "sorted_income_dates" in schedule
    assert "columns" in schedule
    assert "expense_budget_items" in schedule
    assert len(schedule["sorted_income_dates"]) > 0

    # Verify columns use date keys that match sorted_income_dates
    for date_key in schedule["sorted_income_dates"]:
        assert date_key in schedule["columns"], f"Column {date_key} missing from columns dict"
        col = schedule["columns"][date_key]
        assert "incomes" in col
        assert "expenses" in col

    # Verify expenses are in "expenses" not "incomes" (case-sensitivity regression)
    expense_items = schedule["expense_budget_items"]
    assert len(expense_items) > 0, "No expense budget items"

    first_date = schedule["sorted_income_dates"][0]
    col = schedule["columns"][first_date]
    expense_ids_in_col = {e["budget_item"]["id"] for e in col["expenses"]}
    income_ids_in_col = {e["budget_item"]["id"] for e in col["incomes"]}

    for exp_item in expense_items:
        # Expense budget items should NOT appear in incomes
        assert exp_item["id"] not in income_ids_in_col, (
            f"Expense '{exp_item['name']}' (id={exp_item['id']}) found in incomes — "
            "type case-sensitivity regression"
        )


# ---------------------------------------------------------------------------
# Scenario 14: Multiple mark-paid then re-extrapolate
#
# Pay several items across different columns, re-extrapolate, verify
# all paid items survive with correct ledger links.
# ---------------------------------------------------------------------------

def test_multiple_paid_items_survive(app):
    client, db_path = app

    pid = _create_profile(client, "MultiPaid")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-04-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-04-14")

    items = _query_extrapolation_items(db_path, pid)
    # Mark 3 different items as paid
    paid_ids = []
    for item in items[:3]:
        r = client.post(f"/budget/markpaid/{pid}", json={
            "extrapolationItemId": item["id"],
            "accountId": aid,
        })
        assert r.status_code == 200
        paid_ids.append(item["id"])

    # Verify all 3 are paid
    items_after = _query_extrapolation_items(db_path, pid)
    for pid_item in paid_ids:
        paid = next(i for i in items_after if i["id"] == pid_item)
        assert paid["ledger_entry_id"] is not None

    # Re-extrapolate
    _extrapolate(client, pid, "2025-01-15", "2025-04-14")

    items_final = _query_extrapolation_items(db_path, pid)
    for pid_item in paid_ids:
        surviving = next((i for i in items_final if i["id"] == pid_item), None)
        assert surviving is not None, f"Paid item {pid_item} was deleted"
        assert surviving["ledger_entry_id"] is not None


# ---------------------------------------------------------------------------
# Scenario 15: Debt CRUD
#
# Create, read, update, delete a debt.
# ---------------------------------------------------------------------------

def test_debt_crud(app):
    client, _ = app

    pid = _create_profile(client, "DebtTest")["id"]

    # Create
    r = client.post(f"/debts/{pid}", json={
        "name": "Credit Card",
        "total_amount": 5000,
        "remaining_amount": 3000,
        "min_payment": 100,
        "interest_rate": 19.99,
    })
    assert r.status_code == 200
    debt = r.json()
    assert debt["name"] == "Credit Card"
    assert debt["remaining_amount"] == 3000
    debt_id = debt["id"]

    # Read
    r = client.get(f"/debts/{pid}")
    assert r.status_code == 200
    debts = r.json()
    assert len(debts) == 1
    assert debts[0]["id"] == debt_id

    # Update
    r = client.put(f"/debts/{pid}/{debt_id}", json={
        "name": "Credit Card",
        "total_amount": 5000,
        "remaining_amount": 2500,
        "min_payment": 100,
        "interest_rate": 19.99,
    })
    assert r.status_code == 200
    updated = r.json()
    assert updated["remaining_amount"] == 2500

    # Delete
    r = client.delete(f"/debts/{pid}/{debt_id}")
    assert r.status_code == 200

    r = client.get(f"/debts/{pid}")
    assert len(r.json()) == 0


# ---------------------------------------------------------------------------
# Scenario 16: Profile and account deletion cascades
#
# Delete account removes ledger entries. Delete profile removes everything.
# ---------------------------------------------------------------------------

def test_delete_account_cascades(app):
    client, db_path = app

    pid = _create_profile(client, "Cascade")["id"]
    aid = _create_account(client, pid)["id"]

    today = date.today().isoformat()
    client.post(f"/ledger/{pid}", json={
        "account_id": aid,
        "amount": 100,
        "date": today,
        "income_date": today,
    })

    # Verify ledger entry exists
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM ledger_entry WHERE account_id = ?", (aid,)
    ).fetchone()[0]
    conn.close()
    assert count >= 1

    # Delete account
    r = client.delete(f"/accounts/{pid}/{aid}")
    assert r.status_code == 200

    # Ledger entries should be gone
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM ledger_entry WHERE account_id = ?", (aid,)
    ).fetchone()[0]
    conn.close()
    assert count == 0


def test_delete_profile_cascades(app):
    client, db_path = app

    pid = _create_profile(client, "FullCascade")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]
    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )
    _extrapolate(client, pid, "2025-01-15", "2025-02-14")

    # Delete profile
    r = client.delete(f"/profiles/{pid}")
    assert r.status_code == 200

    # Everything should be gone
    conn = sqlite3.connect(db_path)
    for table in ["extrapolation_item", "budget_item", "budget_group", "account"]:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE profile_id = ?", (pid,)
        ).fetchone()[0]
        assert count == 0, f"Expected 0 rows in {table} after profile deletion, got {count}"
    profiles = conn.execute(
        "SELECT COUNT(*) FROM profiles WHERE id = ?", (pid,)
    ).fetchone()[0]
    conn.close()
    assert profiles == 0


# ---------------------------------------------------------------------------
# Scenario 17: Double mark-paid rejected
#
# Marking the same item paid twice should return an error.
# ---------------------------------------------------------------------------

def test_double_mark_paid_rejected(app):
    client, db_path = app

    pid = _create_profile(client, "DoublePay")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-02-14")

    items = _query_extrapolation_items(db_path, pid)
    target_id = items[0]["id"]

    # First mark-paid succeeds
    r = client.post(f"/budget/markpaid/{pid}", json={
        "extrapolationItemId": target_id,
        "accountId": aid,
    })
    assert r.status_code == 200

    # Second mark-paid should fail (either 500 ValueError or 404)
    r2 = client.post(f"/budget/markpaid/{pid}", json={
        "extrapolationItemId": target_id,
        "accountId": aid,
    })
    assert r2.status_code >= 400, (
        f"Double mark-paid should be rejected, got {r2.status_code}"
    )


# ---------------------------------------------------------------------------
# Scenario 18: Debt-linked budget item caps at remaining balance
#
# A $120/month expense linked to a $500 debt should generate payments
# totaling exactly $500 (4 × $120 + 1 × $80), not unlimited $120s.
# ---------------------------------------------------------------------------

def test_debt_linked_budget_item_caps(app):
    client, db_path = app

    pid = _create_profile(client, "DebtCap")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    # Create a debt
    r = client.post(f"/debts/{pid}", json={
        "name": "Credit Card",
        "total_amount": 500,
        "remaining_amount": 500,
        "min_payment": 120,
        "interest_rate": 0,
    })
    assert r.status_code == 200
    debt_id = r.json()["id"]

    # Income so expenses can be scheduled
    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-12-31",
    )

    # Create expense linked to the debt
    r = client.post(f"/budget/{pid}", json={
        "name": "CC Payment",
        "amount": 120,
        "type": "Expense",
        "budget_group_id": gid,
        "start_date": "2025-01-15",
        "end_date": "2025-12-31",
        "periods": [{"type": "Monthly", "value": "1st", "business_day": ""}],
        "debt_id": debt_id,
    })
    assert r.status_code == 200

    _extrapolate(client, pid, "2025-01-15", "2025-12-31")

    items = _query_extrapolation_items(db_path, pid)
    cc_items = [i for i in items if i["amount"] < 0]

    total_paid = sum(abs(i["amount"]) for i in cc_items)
    assert total_paid == pytest.approx(500.0), (
        f"Debt payments should total $500 (the debt balance), got ${total_paid:.2f}"
    )

    # All full payments should be $120, last one should be the remainder
    amounts = sorted([abs(i["amount"]) for i in cc_items], reverse=True)
    full_payments = [a for a in amounts if a == pytest.approx(120.0)]
    remainder_payments = [a for a in amounts if a < 120]

    assert len(remainder_payments) == 1, (
        f"Expected exactly 1 partial (remainder) payment, got {len(remainder_payments)}: {remainder_payments}"
    )
    assert len(full_payments) + len(remainder_payments) == len(cc_items)


# ---------------------------------------------------------------------------
# Scenario 19: Debt-linked item produces zero entries when debt is paid off
#
# If remaining_amount is 0, no payments should be scheduled at all.
# ---------------------------------------------------------------------------

def test_debt_fully_paid_no_entries(app):
    client, db_path = app

    pid = _create_profile(client, "DebtPaid")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    # Debt with 0 remaining
    r = client.post(f"/debts/{pid}", json={
        "name": "Old Loan",
        "total_amount": 1000,
        "remaining_amount": 0,
        "min_payment": 100,
        "interest_rate": 5,
    })
    debt_id = r.json()["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-06-14",
    )

    r = client.post(f"/budget/{pid}", json={
        "name": "Loan Payment",
        "amount": 100,
        "type": "Expense",
        "budget_group_id": gid,
        "start_date": "2025-01-15",
        "end_date": "2025-06-14",
        "periods": [{"type": "Monthly", "value": "1st", "business_day": ""}],
        "debt_id": debt_id,
    })
    assert r.status_code == 200

    _extrapolate(client, pid, "2025-01-15", "2025-06-14")

    items = _query_extrapolation_items(db_path, pid)
    loan_items = [i for i in items if i["amount"] < 0]

    assert len(loan_items) == 0, (
        f"Fully paid debt should produce 0 expense entries, got {len(loan_items)}"
    )


# ---------------------------------------------------------------------------
# Scenario 20: Debt-linked item with small remaining balance
#
# $50 remaining on a $200/month payment → single $50 payment.
# ---------------------------------------------------------------------------

def test_debt_small_remaining_single_payment(app):
    client, db_path = app

    pid = _create_profile(client, "DebtSmall")["id"]
    _create_account(client, pid)
    gid = _create_group(client, pid)["id"]

    r = client.post(f"/debts/{pid}", json={
        "name": "Store Card",
        "total_amount": 500,
        "remaining_amount": 50,
        "min_payment": 200,
        "interest_rate": 0,
    })
    debt_id = r.json()["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-06-14",
    )

    r = client.post(f"/budget/{pid}", json={
        "name": "Store Payment",
        "amount": 200,
        "type": "Expense",
        "budget_group_id": gid,
        "start_date": "2025-01-15",
        "end_date": "2025-06-14",
        "periods": [{"type": "Monthly", "value": "1st", "business_day": ""}],
        "debt_id": debt_id,
    })
    assert r.status_code == 200

    _extrapolate(client, pid, "2025-01-15", "2025-06-14")

    items = _query_extrapolation_items(db_path, pid)
    store_items = [i for i in items if i["amount"] < 0]

    assert len(store_items) == 1, (
        f"Expected exactly 1 payment for $50 remaining, got {len(store_items)}"
    )
    assert abs(store_items[0]["amount"]) == pytest.approx(50.0), (
        f"Single payment should be $50 (remaining balance), got ${abs(store_items[0]['amount']):.2f}"
    )


# ---------------------------------------------------------------------------
# Scenario 21: Reconciliation — parse CSV
#
# Upload a CSV string, verify it parses correctly and detects columns.
# ---------------------------------------------------------------------------

def test_reconcile_parse_csv(app):
    client, _ = app

    pid = _create_profile(client, "Recon1")["id"]

    csv_content = """Date,Amount,Description
2025-02-01,-1000.00,Rent Payment
2025-02-05,-300.00,Car Insurance
2025-02-10,2000.00,Paycheck Deposit
"""
    r = client.post(f"/reconcile/{pid}/parse", json={
        "csv_content": csv_content,
    })
    assert r.status_code == 200
    data = r.json()

    assert data["count"] == 3
    assert data["detected_columns"]["date"] == "Date"
    assert data["detected_columns"]["amount"] == "Amount"
    assert data["detected_columns"]["description"] == "Description"

    # Verify parsed transactions
    txns = data["transactions"]
    assert txns[0]["date"] == "2025-02-01"
    assert txns[0]["amount"] == -1000.0
    assert txns[1]["amount"] == -300.0
    assert txns[2]["amount"] == 2000.0


# ---------------------------------------------------------------------------
# Scenario 22: Reconciliation — auto-match transactions to extrapolation items
#
# Create budget items, extrapolate, then match bank transactions against
# the unpaid extrapolation items.
# ---------------------------------------------------------------------------

def test_reconcile_match_transactions(app):
    client, db_path = app

    pid = _create_profile(client, "Recon2")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-03-14")

    # Get the extrapolation items to know what due dates were created
    items = _query_extrapolation_items(db_path, pid)
    rent_items = [i for i in items if i["amount"] < 0]
    assert len(rent_items) > 0

    # Bank CSV with a rent payment close to the due date
    rent_due = rent_items[0]["due_date"]
    transactions = [
        {"date": rent_due, "amount": -1000.0, "description": "RENT AUTOPAY"},
    ]

    r = client.post(f"/reconcile/{pid}/match", json={
        "transactions": transactions,
        "account_id": aid,
    })
    assert r.status_code == 200
    data = r.json()
    matches = data["matches"]

    assert len(matches) == 1
    assert matches[0]["status"] == "matched"
    assert matches[0]["match"]["confidence"] >= 50, (
        f"Expected reasonable confidence, got {matches[0]['match']['confidence']}%"
    )


# ---------------------------------------------------------------------------
# Scenario 23: Reconciliation — unmatched transaction stays unmatched
#
# A bank transaction with no close extrapolation item should be unmatched.
# ---------------------------------------------------------------------------

def test_reconcile_unmatched_transaction(app):
    client, _ = app

    pid = _create_profile(client, "Recon3")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    # Create a small budget — income only, no expenses
    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-02-14",
    )
    _extrapolate(client, pid, "2025-01-15", "2025-02-14")

    # Bank transaction that doesn't match anything (random coffee purchase)
    transactions = [
        {"date": "2025-01-20", "amount": -4.50, "description": "STARBUCKS"},
    ]

    r = client.post(f"/reconcile/{pid}/match", json={
        "transactions": transactions,
        "account_id": aid,
    })
    assert r.status_code == 200
    data = r.json()
    matches = data["matches"]

    assert len(matches) == 1
    assert matches[0]["status"] == "unmatched"
    assert matches[0]["match"] is None


# ---------------------------------------------------------------------------
# Scenario 24: Reconciliation — import confirmed matches
#
# Confirm a matched transaction → creates ledger entry and links to
# the extrapolation item (marks it paid).
# ---------------------------------------------------------------------------

def test_reconcile_import_marks_paid(app):
    client, db_path = app

    pid = _create_profile(client, "Recon4")["id"]
    aid = _create_account(client, pid)["id"]
    gid = _create_group(client, pid)["id"]

    _create_budget_item(
        client, pid, gid,
        name="Salary", amount=3000, item_type="Income",
        periods=[{"type": "Monthly", "value": "15th", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )
    _create_budget_item(
        client, pid, gid,
        name="Rent", amount=1000, item_type="Expense",
        periods=[{"type": "Monthly", "value": "1st", "business_day": ""}],
        start="2025-01-15", end="2025-03-14",
    )

    _extrapolate(client, pid, "2025-01-15", "2025-03-14")

    # Find a rent extrapolation item
    items = _query_extrapolation_items(db_path, pid)
    rent_item = next(i for i in items if i["amount"] < 0)
    assert rent_item["ledger_entry_id"] is None, "Should be unpaid before import"

    # Match
    transactions = [
        {"date": rent_item["due_date"], "amount": -1000.0, "description": "RENT"},
    ]
    r = client.post(f"/reconcile/{pid}/match", json={
        "transactions": transactions,
        "account_id": aid,
    })
    data = r.json()
    matches = data["matches"]
    assert matches[0]["status"] == "matched"
    extrap_id = matches[0]["match"]["extrapolation_item_id"]

    # Import
    r = client.post(f"/reconcile/{pid}/import", json={
        "account_id": aid,
        "confirmed": [{
            "transaction": transactions[0],
            "extrapolation_item_id": extrap_id,
        }],
    })
    assert r.status_code == 200
    result = r.json()
    assert result["imported"] == 1
    assert result["linked"] == 1

    # Verify the extrapolation item is now paid
    items_after = _query_extrapolation_items(db_path, pid)
    paid_item = next(i for i in items_after if i["id"] == extrap_id)
    assert paid_item["ledger_entry_id"] is not None, "Should be linked after import"


# ---------------------------------------------------------------------------
# Scenario 25: Reconciliation — import standalone (unmatched) transaction
#
# Import an unmatched transaction without linking to an extrapolation item.
# Should create a ledger entry against the account.
# ---------------------------------------------------------------------------

def test_reconcile_import_standalone(app):
    client, db_path = app

    pid = _create_profile(client, "Recon5")["id"]
    aid = _create_account(client, pid)["id"]

    # Import a standalone transaction (no budget match)
    r = client.post(f"/reconcile/{pid}/import", json={
        "account_id": aid,
        "confirmed": [{
            "transaction": {
                "date": "2025-02-15",
                "amount": -25.00,
                "description": "GROCERY STORE",
            },
            "extrapolation_item_id": None,
        }],
    })
    assert r.status_code == 200
    result = r.json()
    assert result["imported"] == 1
    assert result["linked"] == 0

    # Verify ledger entry was created
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM ledger_entry WHERE account_id = ?", (aid,)
    ).fetchone()[0]
    conn.close()
    assert count >= 1


# ---------------------------------------------------------------------------
# Scenario 26: Reconciliation — CSV column auto-detection with various formats
#
# Test that the parser handles different date/amount formats.
# ---------------------------------------------------------------------------

def test_reconcile_csv_formats(app):
    client, _ = app

    pid = _create_profile(client, "Recon6")["id"]

    # CSV with MM/DD/YYYY dates, $amounts with commas, parentheses for negatives
    csv_content = """Transaction Date,Transaction Amount,Memo
02/15/2025,$2000.00,PAYCHECK
02/01/2025,($1000.00),RENT PAYMENT
02/05/2025,"($1,250.50)",CAR PAYMENT
"""
    r = client.post(f"/reconcile/{pid}/parse", json={
        "csv_content": csv_content,
    })
    assert r.status_code == 200
    data = r.json()

    assert data["count"] == 3
    txns = data["transactions"]

    # Check date parsing (MM/DD/YYYY → YYYY-MM-DD)
    assert txns[0]["date"] == "2025-02-15"
    assert txns[1]["date"] == "2025-02-01"

    # Check amount parsing ($, commas, parentheses)
    assert txns[0]["amount"] == pytest.approx(2000.0)
    assert txns[1]["amount"] == pytest.approx(-1000.0)
    assert txns[2]["amount"] == pytest.approx(-1250.50)
