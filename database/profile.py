from datetime import date, datetime


class Profile:
    id: int = None
    name: str = None
    hidden_through: datetime = None
    created_at: datetime = None

    def __init__(self, name, id=None, created_at=None, hidden_through=None):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.hidden_through = hidden_through

    def create(self, db):
        cursor = db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            "INSERT INTO profiles (name, created_at, hidden_through) VALUES (?, ?, NULL)",
            (self.name, datetime_now),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.created_at = datetime_now

    staticmethod

    def update_hidden_through(self, db, hidden_through):
        self.hidden_through = hidden_through
        cursor = db.cursor()
        cursor.execute(
            "UPDATE profiles SET hidden_through = ? WHERE id = ?", (hidden_through, self.id)
        )
        db.commit()

    def fetch_all(db):
        cursor = db.cursor()
        cursor.execute("SELECT name, id, created_at, hidden_through FROM profiles")
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(
                Profile(
                    row[0],
                    row[1],
                    datetime.fromisoformat(row[2]),
                    date.fromisoformat(row[3]) if row[3] else None,
                )
            )
        return output

    staticmethod

    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "profiles" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "hidden_through" date NULL,
                "created_at" datetime NOT NULL);
        """
        )
        db.commit()
