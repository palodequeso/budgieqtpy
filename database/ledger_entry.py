from datetime import date, datetime


class LedgerEntry:
    id: int = None
    name: str = None
    paid_date: date = None
    income_date: date = None
    type: str = None
    amount: float = None
    account_id: int = None
    created_at: datetime = None
    updated_at: datetime = None

    def __init__(
        self,
        name,
        paid_date,
        income_date,
        type,
        amount,
        account_id,
        id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.name = name
        self.paid_date = paid_date
        self.income_date = income_date
        self.type = type
        self.amount = amount
        self.created_at = created_at
        self.updated_at = updated_at
        self.account_id = account_id

    def create(self, db):
        cursor = db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            INSERT INTO ledger_entry
            (name, paid_date, income_date, type, amount, account_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.name,
                self.paid_date.strftime("%Y-%m-%d"),
                self.income_date.strftime("%Y-%m-%d"),
                self.type,
                self.amount,
                self.account_id,
                datetime_now,
                datetime_now,
            ),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.createdAt = datetime_now
        self.updatedAt = datetime_now

    @staticmethod
    def fetch_by_account(db, account_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT name, paid_date, income_date, type, amount, account_id, id, created_at, updated_at FROM ledger_entry WHERE account_id = ?",
            (account_id,),
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(
                LedgerEntry(
                    row[0],
                    datetime.fromisoformat(row[1]),
                    datetime.fromisoformat(row[2]),
                    row[3],
                    row[4],
                    row[5],
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
            CREATE TABLE IF NOT EXISTS "ledger_entry" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "paid_date" datetime NOT NULL,
                "income_date" datetime,
                "type" varchar NOT NULL,
                "amount" decimal(12,2) NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "account_id" integer,
                CONSTRAINT "FK_d02a6aa67832567d5866141bc0e" FOREIGN KEY ("account_id")
                REFERENCES "account" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION)
        """
        )
        db.commit()
