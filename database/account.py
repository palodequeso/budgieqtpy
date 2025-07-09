from datetime import datetime

from database.ledger_entry import LedgerEntry


class Account:
    id: int = None
    name: str = None
    account_type: str = None
    balance: float = None
    created_at: datetime = None
    updated_at: datetime = None

    def __init__(self, name, account_type, id=None, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.account_type = account_type
        self.balance = 0
        self.created_at = created_at
        self.updated_at = updated_at

    def create(self, db, profile_id):
        cursor = db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            INSERT INTO account
            (name, type, profile_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (self.name, self.account_type, profile_id, datetime_now, datetime_now),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.created_at = datetime_now
        self.updated_at = datetime_now

        # create starting balance ledger entry
        ledger = LedgerEntry(
            "Starting Balance",
            datetime_now,
            datetime_now,
            "Income",
            self.balance,
            self.id,
        )
        ledger.create(db)

    staticmethod

    def fetch_all(db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT name, type, id, created_at, updated_at FROM account WHERE profile_id = ?",
            (profile_id,),
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(
                Account(
                    row[0],
                    row[1],
                    row[2],
                    datetime.fromisoformat(row[3]),
                    datetime.fromisoformat(row[4]),
                )
            )
        return output

    staticmethod

    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "account" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "type" varchar NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "profile_id" integer,
                CONSTRAINT "FK_ff102ecfd2f4b5a7edf239dd025"
                FOREIGN KEY ("profile_id") REFERENCES "profile" ("id")
                ON DELETE NO ACTION ON UPDATE NO ACTION)
        """
        )
        db.commit()
