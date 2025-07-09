from datetime import date, datetime


class ExtrapolationItem:
    id: int = None
    due_date: date = None
    amount: float = None
    income_date: date = None
    created_at: datetime = None
    updated_at: datetime = None
    overridden_at: date = None
    budget_item_id: int = None
    ledger_entry_id: int = None

    def __init__(
        self,
        due_date,
        amount,
        income_date,
        budget_item_id,
        overridden_at=None,
        ledger_entry_id=None,
        id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.due_date = due_date
        self.amount = amount
        self.income_date = income_date
        self.created_at = created_at
        self.updated_at = updated_at
        self.overridden_at = overridden_at
        self.budget_item_id = budget_item_id
        self.ledger_entry_id = ledger_entry_id

    def create(self, db, profile_id):
        cursor = db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            INSERT INTO extrapolation_item
            (due_date, amount, income_date, created_at, updated_at, budget_item_id, profile_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.due_date,
                self.amount,
                self.income_date,
                datetime_now,
                datetime_now,
                self.budget_item_id,
                profile_id,
            ),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.created_at = datetime_now
        self.updated_at = datetime_now

    @staticmethod
    def update_ledger_entry_id(db, extrapolation_item_id, ledger_entry_id):
        cursor = db.cursor()
        cursor.execute(
            "UPDATE extrapolation_item SET ledger_entry_id = ? WHERE id = ?",
            (ledger_entry_id, extrapolation_item_id),
        )
        db.commit()

    @staticmethod
    def clear(db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM extrapolation_item WHERE profile_id = ?", (profile_id,)
        )
        db.commit()

    @staticmethod
    def fetch_all(db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT due_date, amount, income_date, budget_item_id, overridden_at, ledger_entry_id, id, created_at, updated_at FROM extrapolation_item WHERE profile_id = ?",
            (profile_id,),
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(
                ExtrapolationItem(
                    date.fromisoformat(row[0]),
                    row[1],
                    date.fromisoformat(row[2]),
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    datetime.fromisoformat(row[7]),
                    datetime.fromisoformat(row[8]),
                )
            )
        return output

    @staticmethod
    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "extrapolation_item" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "due_date" datetime NOT NULL,
                "amount" decimal(12,2) NOT NULL,
                "income_date" datetime,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "overridden_at" datetime,
                "budget_item_id" integer,
                "ledger_entry_id" integer,
                "profile_id" integer,
                CONSTRAINT "REL_6e4d51fad1f2bdc128e4031154" UNIQUE ("ledger_entry_id"),
                CONSTRAINT "FK_d5addf4fde8c9b808450b32cc51" FOREIGN KEY ("budget_item_id")
                REFERENCES "budget_item" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION,
                CONSTRAINT "FK_6e4d51fad1f2bdc128e40311547" FOREIGN KEY ("ledger_entry_id")
                REFERENCES "ledger_entry" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION,
                CONSTRAINT "FK_cd88bf9c93ec5bcfd8bb8e85155" FOREIGN KEY ("profile_id")
                REFERENCES "profile" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION)
        """
        )
        db.commit()
