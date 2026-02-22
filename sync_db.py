import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

def run_command(cmd):
    print(f"Running: {cmd}")
    env = os.environ.copy()
    # Explicitly set DATABASE_URL if not found or to be sure
    if "DATABASE_URL" not in env:
        env["DATABASE_URL"] = "postgresql://postgres:123456@localhost:5432/nexprime_db"
    
    result = subprocess.run(cmd, env=env, shell=True, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    return result.returncode

if __name__ == "__main__":
    print("Attempting to sync database...")
    if run_command("npx prisma db push") == 0:
        print("Database synced successfully.")
        print("Generating Prisma client...")
        run_command("npx prisma generate")
    else:
        print("Database sync failed.")
