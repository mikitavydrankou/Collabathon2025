import os

from shared.seed import seed_database

if __name__ == "__main__":
    if os.getenv("SEED_ON_START", "false").lower() in ("1", "true", "yes"):
        seed_database()
    else:
        print("SEED_ON_START not set; skipping seed")
