# Integration Test Plan

## Approach

- `pytest` (installed in `venv/`)
- FastAPI `TestClient` — no running server needed, synchronous
- Each test gets a fresh SQLite file via `tmp_path` fixture
- Tests hit real endpoints: create data → modify → assert

Run with: `venv/bin/python -m pytest tests/ -v`

## Step 1: Fix Database for test isolation

`database/database.py` has a class-level connection opened at import time:
```python
DB_PATH = os.getenv('DATABASE_PATH', 'budgie.db')
db = sqlite3.connect(DB_PATH)
```

Move both into `__init__` so env-var override works per-test:
```python
def __init__(self, db_path: str = None):
    path = db_path or os.getenv('DATABASE_PATH', 'budgie.db')
    self.db = sqlite3.connect(path)
    self.create_tables()
```

## Step 2: conftest.py

```python
# tests/conftest.py
import os, pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    from backend.server import Server
    with TestClient(Server.app) as c:
        yield c
```

> Note: `Server.app` is a module-level singleton — import it inside the fixture
> so the env var is set before any `Database()` is instantiated.

## Step 3: Scenarios

### 1. Profile CRUD (smoke test)
- POST `/profiles` → create profile
- GET `/profiles` → verify it appears
- Check `id`, `name` fields

### 2. Account balance
- Create profile + account
- POST `/ledger/{profile_id}` → add $500 entry
- GET `/profiles/{profile_id}` → verify account balance = 500

### 3. Monthly extrapolation — item count
- Create profile, account, budget group
- Create expense item: Monthly, "1st", $300, no business day
- POST `/extrapolate/{profile_id}` with 3-month range
- GET `/schedule/{profile_id}` → item count = 3

### 4. Income + expenses — net balance math
- $2000 income on 15th, $1000 rent on 1st, $100 insurance on 1st
- Extrapolate 3 months
- Group schedule by income_date
- Each column: incomeTotal=2000, expenseTotal=1100, net=900
- Verifies the sign fix (expenses stored as negative)

### 5. Multiple periods — paid twice a month
- Income item with two periods: "15th" and "Last"
- Extrapolate 2 months
- Assert: 4 income extrapolation items created

### 6. "Last" day of month
- Monthly item on "Last"
- Extrapolate covering Feb, Mar, Apr
- Assert dates: Feb 28 (or 29), Mar 31, Apr 30

### 7. Business day adjustment
- Find a month where the 15th is a Saturday or Sunday
- Item: Monthly, "15th", business_day="Previous"
- Assert: extrapolation date lands on the preceding Friday

### 8. Mark paid → re-extrapolate (regression test for known bug)
- Create income item, extrapolate
- Mark one income item as received → `ledger_entry_id` set
- Re-run extrapolation
- **Expected (correct):** paid item not duplicated, ledger link preserved
- **Current behaviour:** paid item is wiped and recreated unpaid
- Mark this test `@pytest.mark.xfail` until the bug is fixed

### 9. Savings mark-paid → correct account balance
- Run compute savings, save entries
- Mark a savings extrapolation item as paid against a savings account
- Verify savings account balance increased (positive), not decreased
- Verifies the `abs(amount)` fix in `ledger_service.py`

## Key facts

- Expense amounts stored as **negative** in `extrapolation_item.amount`
- `budget_item_period.value` is a **string**: "1st"–"28th" or "Last"
- `budget_item_period.business_day`: "Previous" / "Next" / ""
- `clear_extrapolation_items` deletes ALL items including paid ones (the bug in scenario 8)
- Account balance = sum of all `ledger_entry.amount` for that account
