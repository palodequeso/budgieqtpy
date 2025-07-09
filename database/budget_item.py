from datetime import date, datetime
from .budget_item_period import BudgetItemPeriod


class BudgetItem:
    id: int = None
    name: str = None
    type: str = None
    amount: float = None
    created_at: datetime = None
    updated_at: datetime = None
    start_date: date = None
    end_date: date = None
    budget_group_id: int = None
    periods: list[BudgetItemPeriod] = None

    def __init__(
        self,
        name,
        type,
        amount,
        start_date,
        end_date,
        budget_group_id,
        periods,
        id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.amount = amount
        self.created_at = created_at
        self.updated_at = updated_at
        self.start_date = start_date
        self.end_date = end_date
        self.budget_group_id = budget_group_id
        self.periods = periods

    def create(self, db, profile_id):
        datetime_now = datetime.now()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO budget_item
            (name, type, amount, budget_group_id, start_date, end_date, profile_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.name,
                self.type,
                self.amount,
                self.budget_group_id,
                self.start_date,
                self.end_date,
                profile_id,
                datetime_now,
                datetime_now,
            ),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.created_at = datetime_now
        self.updated_at = datetime_now

        created_periods = []
        for period in self.periods:
            p = BudgetItemPeriod(period.type, period.value, period.business_day, self.id)
            p.create(db)
            created_periods.append(p)
        self.periods = created_periods

    staticmethod

    def fetch_all(db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT name, type, amount, start_date, end_date, budget_group_id, id, created_at, updated_at FROM budget_item WHERE profile_id = ?",
            (profile_id,),
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            periods = BudgetItemPeriod.fetch_by_budget_item(db, row[6])
            output.append(
                BudgetItem(
                    row[0],
                    row[1],
                    row[2],
                    date.fromisoformat(row[3]),
                    date.fromisoformat(row[4]),
                    row[5],
                    periods,
                    row[6],
                    datetime.fromisoformat(row[7]),
                    datetime.fromisoformat(row[8]),
                )
            )
        return output

    staticmethod

    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "budget_item" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "type" varchar NOT NULL,
                "amount" decimal(12,2) NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "start_date" datetime NOT NULL,
                "end_date" datetime,
                "profile_id" integer,
                "budget_group_id" integer,
                CONSTRAINT "FK_5dc7f314b4ade58360201376c1b" FOREIGN KEY ("profile_id")
                REFERENCES "profile" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION,
                CONSTRAINT "FK_1b438ee1e05d339529bb22fc80a" FOREIGN KEY ("budget_group_id")
                REFERENCES "budget_group" ("id") ON DELETE CASCADE ON UPDATE NO ACTION)
        """
        )
        db.commit()
