import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from chatbot.models import Category, KnowledgeBase

class Command(BaseCommand):
    help = "Imports knowledge base entries and categories from the seed JSON file into Neon PostgreSQL."

    def handle(self, *args, **options):
        self.stdout.write("Starting chatbot KnowledgeBase and Category import...")

        # Locate seed JSON file
        json_path = os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'knowledge_entries.json')
        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR(f"Seed file not found at: {json_path}"))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to read or parse JSON seed file: {str(e)}"))
            return

        total_records = len(entries)
        created_categories = 0
        created_knowledge = 0
        updated_knowledge = 0
        failed_records = 0

        self.stdout.write(f"Parsed {total_records} records from JSON. Commencing database insertion...")

        # Atomically execute imports
        with transaction.atomic():
            for idx, entry in enumerate(entries):
                try:
                    category_name = entry.get('category')
                    question = entry.get('question')
                    answer = entry.get('answer')
                    title = entry.get('title')

                    # Simple validation
                    if not category_name or not question or not answer or not title:
                        self.stderr.write(
                            self.style.WARNING(
                                f"Row {idx + 1} validation failed: Category, Question, Answer, and Title are required. Skipping."
                            )
                        )
                        failed_records += 1
                        continue

                    # 1. Fetch or create Category
                    cat_obj, cat_created = Category.objects.get_or_create(
                        name=category_name.strip(),
                        defaults={"description": f"Seeded category for {category_name}"}
                    )
                    if cat_created:
                        created_categories += 1

                    # 2. Insert or update KnowledgeBase Q&A entry
                    kb_obj, kb_created = KnowledgeBase.objects.update_or_create(
                        question=question.strip(),
                        defaults={
                            'title': title.strip(),
                            'category': cat_obj,
                            'answer': answer.strip(),
                            'keywords': entry.get('keywords', '').strip(),
                            'synonyms': entry.get('synonyms', '').strip(),
                            'priority': entry.get('priority', 0),
                            'difficulty': entry.get('difficulty', 'Medium').strip(),
                            'tags': entry.get('tags', '').strip(),
                            'is_active': entry.get('is_active', True)
                        }
                    )

                    if kb_created:
                        created_knowledge += 1
                    else:
                        updated_knowledge += 1

                except Exception as row_error:
                    self.stderr.write(
                        self.style.ERROR(
                            f"Fatal database error seeding row {idx + 1} ('{entry.get('title', 'Unknown')}'): {str(row_error)}"
                        )
                    )
                    failed_records += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n--- IMPORT STATISTICS ---\n"
                f"Total parsed rows: {total_records}\n"
                f"Categories created: {created_categories}\n"
                f"KnowledgeBase created: {created_knowledge}\n"
                f"KnowledgeBase updated: {updated_knowledge}\n"
                f"Validation / DB failures: {failed_records}\n"
                f"Active categories in DB: {Category.objects.count()}\n"
                f"Active Q&A entries in DB: {KnowledgeBase.objects.filter(is_active=True).count()}\n"
                f"-------------------------\n"
            )
        )
