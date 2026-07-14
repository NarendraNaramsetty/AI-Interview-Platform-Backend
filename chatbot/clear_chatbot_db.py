import os
import sys
import glob
import django
from django.db import connection

# Append current working directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def clear_db():
    print("Dropping chatbot tables from database...")
    tables = [
        "chatbot_feedback",
        "chatbot_chatfeedback",
        "chatbot_adminanalytics",
        "chatbot_knowledgebase",
        "chatbot_chatmessage",
        "chatbot_chatsession",
        "chatbot_chatbookmark",
        "chatbot_chathistory",
        "chatbot_prompttemplate",
        "chatbot_category"
    ]
    with connection.cursor() as cursor:
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {str(e)}")
                
    # Clear migrations entry from django_migrations
    with connection.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'chatbot';")
            print("Cleared migration history for app 'chatbot'")
        except Exception as e:
            print(f"Error clearing migration history: {str(e)}")

def clear_migration_files():
    print("Clearing migration files...")
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    files = glob.glob(os.path.join(migrations_dir, '00*.py'))
    for f in files:
        try:
            os.remove(f)
            print(f"Removed {os.path.basename(f)}")
        except Exception as e:
            print(f"Error removing {f}: {str(e)}")

if __name__ == "__main__":
    clear_db()
    clear_migration_files()
    print("Completed reset successfully!")
