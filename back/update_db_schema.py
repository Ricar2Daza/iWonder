from sqlalchemy import create_engine, text
from core.config import settings

def add_columns():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists or just try to add it (Postgres will fail if it exists)
            conn.execute(text("ALTER TABLE users ADD COLUMN bio VARCHAR"))
            print("Added bio column")
        except Exception as e:
            print(f"Bio column error (maybe exists): {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
            print("Added avatar_url column")
        except Exception as e:
            print(f"Avatar_url column error (maybe exists): {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_content_type VARCHAR"))
            print("Added avatar_content_type column")
        except Exception as e:
            print(f"Avatar_content_type column error (maybe exists): {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_size INTEGER"))
            print("Added avatar_size column")
        except Exception as e:
            print(f"Avatar_size column error (maybe exists): {e}")
            
        conn.commit()

if __name__ == "__main__":
    add_columns()