import os
import sys
import subprocess
import django
from django.core.management import call_command

def dump_data():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urban_service.settings')
    django.setup()
    
    print("Dumping data directly using utf-8...")
    with open("datadump_clean.json", "w", encoding="utf-8") as f:
        call_command(
            "dumpdata", 
            format="json", 
            indent=4, 
            natural_foreign=True, 
            natural_primary=True, 
            exclude=["contenttypes", "auth.Permission", "sessions.Session", "admin.logentry"], 
            stdout=f
        )
    print("Local dump finished perfectly!")

def load_remote():
    print("Preparing to load remote database over Render...")
    env_remote = os.environ.copy()
    env_remote["PYTHONUTF8"] = "1"

    # Load DATABASE_URL from environment — NEVER hardcode credentials here.
    # Set DATABASE_URL in your .env file or shell before running this script.
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise EnvironmentError(
            "DATABASE_URL is not set. "
            "Export it in your shell or add it to your .env file before running this script.\n"
            "  Example: set DATABASE_URL=postgresql://user:password@host/dbname"
        )
    env_remote["DATABASE_URL"] = db_url
    
    print("1. Migrating schema remotely...")
    subprocess.run([sys.executable, "manage.py", "migrate"], env=env_remote, check=True)
    
    print("2. Pushing data remotely...")
    subprocess.run([sys.executable, "manage.py", "loaddata", "datadump_clean.json"], env=env_remote, check=True)
    print("Data migration successful over the cloud!")

if __name__ == '__main__':
    dump_data()
    load_remote()
