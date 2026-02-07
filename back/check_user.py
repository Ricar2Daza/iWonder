
from sqlalchemy import create_engine, text
from core.config import settings

def check_user(username):
    try:
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
        with engine.connect() as connection:
            print(f"Checking for username: '{username}'")
            result = connection.execute(text("SELECT id, username, email FROM users WHERE username = :username"), {"username": username})
            user = result.fetchone()
            if user:
                print(f"User found: {user}")
            else:
                print("User not found")
                
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    check_user("user")
    check_user("User")
