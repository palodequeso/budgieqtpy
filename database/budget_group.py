class BudgetGroup:
    id: int = None
    name: str = None

    def __init__(self, name, id=None):
        self.id = id
        self.name = name

    def create(self, db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO budget_group (name, profile_id) VALUES (?, ?)",
            (self.name, profile_id),
        )
        db.commit()
        self.id = cursor.lastrowid

    staticmethod

    def fetch_all(db, profile_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT name, id FROM budget_group WHERE profile_id = ?", (profile_id,)
        )
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(BudgetGroup(row[0], row[1]))
        return output

    staticmethod

    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "budget_group" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "profile_id" integer,
                CONSTRAINT "FK_3648fb7c8e5a00073a94b0a9c1d" FOREIGN KEY ("profile_id")
                REFERENCES "profile" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION)
        """
        )
        db.commit()
