from datetime import datetime


class Debt:
    id: int = None
    name: str = None
    total_amount: float = None
    remaining_amount: float = None
    min_payment: float = None
    interest_rate: float = None
    profile_id: int = None
    created_at: datetime = None
    updated_at: datetime = None

    def __init__(
        self,
        name,
        total_amount,
        remaining_amount,
        min_payment,
        interest_rate,
        profile_id=None,
        id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.name = name
        self.total_amount = total_amount
        self.remaining_amount = remaining_amount
        self.min_payment = min_payment
        self.interest_rate = interest_rate
        self.profile_id = profile_id
        self.created_at = created_at
        self.updated_at = updated_at

    def create(self, db, profile_id):
        datetime_now = datetime.now()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO debt
            (name, total_amount, remaining_amount, min_payment, interest_rate, profile_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.name,
                self.total_amount,
                self.remaining_amount,
                self.min_payment,
                self.interest_rate,
                profile_id,
                datetime_now,
                datetime_now,
            ),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.profile_id = profile_id
        self.created_at = datetime_now
        self.updated_at = datetime_now

    @staticmethod
    def fetch_all(db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT name, total_amount, remaining_amount, min_payment, interest_rate, profile_id, id, created_at, updated_at FROM debt WHERE profile_id = ?",
            (profile_id,),
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            created_at = datetime.fromisoformat(row[7]) if row[7] and isinstance(row[7], str) else row[7]
            updated_at = datetime.fromisoformat(row[8]) if row[8] and isinstance(row[8], str) else row[8]
            output.append(
                Debt(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    created_at,
                    updated_at,
                )
            )
        return output

    @staticmethod
    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "debt" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "total_amount" decimal(12,2) NOT NULL,
                "remaining_amount" decimal(12,2) NOT NULL,
                "min_payment" decimal(12,2) NOT NULL DEFAULT 0,
                "interest_rate" decimal(5,4) NOT NULL DEFAULT 0,
                "profile_id" integer,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                CONSTRAINT "FK_debt_profile" FOREIGN KEY ("profile_id")
                REFERENCES "profile" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION)
        """
        )
        db.commit()
