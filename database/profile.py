from datetime import date, datetime


class Profile:
    id: int = None
    name: str = None
    hidden_through: datetime = None
    created_at: datetime = None
    theme: str = None

    def __init__(self, name, id=None, created_at=None, hidden_through=None, theme="dark"):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.hidden_through = hidden_through
        self.theme = theme if theme else "dark"

    def create(self, db):
        cursor = db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            "INSERT INTO profiles (name, created_at, hidden_through, theme) VALUES (?, ?, NULL, ?)",
            (self.name, datetime_now, self.theme),
        )
        db.commit()
        self.id = cursor.lastrowid
        self.created_at = datetime_now

    @staticmethod
    def update_hidden_through(self, db, hidden_through):
        self.hidden_through = hidden_through
        cursor = db.cursor()
        cursor.execute(
            "UPDATE profiles SET hidden_through = ? WHERE id = ?", (hidden_through, self.id)
        )
        db.commit()
    
    def update_theme(self, db, theme):
        """Update the theme preference for this profile."""
        self.theme = theme
        cursor = db.cursor()
        cursor.execute(
            "UPDATE profiles SET theme = ? WHERE id = ?", (theme, self.id)
        )
        db.commit()

    def from_row(row):
        """Create a Profile instance from a database row."""
        return Profile(
            row[1],  # name
            row[0],  # id
            datetime.fromisoformat(row[4]),  # created_at
            date.fromisoformat(row[2]) if row[2] else None,  # hidden_through
            row[3] if row[3] else "dark",  # theme
        )

    def fetch_all(db):
        cursor = db.cursor()
        cursor.execute("SELECT id, name, hidden_through, theme, created_at FROM profiles")
        rows = cursor.fetchall()
        output = []
        for row in rows:
            output.append(Profile.from_row(row))
        return output

    @staticmethod
    def create_table(db):
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "profiles" (
                "id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" varchar NOT NULL,
                "hidden_through" date NULL,
                "created_at" datetime NOT NULL,
                "theme" varchar DEFAULT 'dark');
        """
        )
        db.commit()
        
        # Add theme column to existing tables (migration)
        try:
            cursor.execute("ALTER TABLE profiles ADD COLUMN theme varchar DEFAULT 'dark'")
            db.commit()
        except:
            pass  # Column already exists
