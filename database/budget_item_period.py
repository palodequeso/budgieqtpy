from datetime import datetime


class BudgetItemPeriod:
    id: int = None
    created_at: datetime = None
    updated_at: datetime = None
    type: str = None
    value: str = None
    business_day: str = None
    budget_item_id: int = None

    def __init__(
        self,
        type,
        value,
        business_day,
        budget_item_id,
        id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at
        self.type = type
        self.value = value
        self.business_day = business_day
        self.budget_item_id = budget_item_id

    def create(self, db):
        cursor = db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            INSERT INTO budget_item_period
            (type, value, business_day, budget_item_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.type,
                self.value,
                self.business_day,
                self.budget_item_id,
                datetime_now,
                datetime_now,
            ),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.created_at = datetime_now
        self.updated_at = datetime_now

    staticmethod

    def fetch_by_budget_item(db, budget_item_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT type, value, business_day, budget_item_id, id, created_at, updated_at FROM budget_item_period WHERE budget_item_id = ?",
            (budget_item_id,),
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(
                BudgetItemPeriod(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    datetime.fromisoformat(row[5]),
                    datetime.fromisoformat(row[6]),
                )
            )
        return output

    staticmethod

    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "budget_item_period" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "type" varchar NOT NULL,
                "value" varchar NOT NULL,
                "business_day" varchar NOT NULL,
                "budget_item_id" integer,
                CONSTRAINT "FK_724758b18cd45a0de754035fd02" FOREIGN KEY ("budget_item_id")
                REFERENCES "budget_item" ("id") ON DELETE CASCADE ON UPDATE NO ACTION)
        """
        )
        db.commit()
