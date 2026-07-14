import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from chatbot.models import KnowledgeBase

class Command(BaseCommand):
    help = "Seeds the chatbot local KnowledgeBase from knowledge_entries.json"

    def handle(self, *args, **options):
        self.stdout.write("Starting chatbot KnowledgeBase seeding...")

        # Construct path to seed data file
        json_path = os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'knowledge_entries.json')
        
        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR(f"Seed file not found at {json_path}"))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading seed JSON file: {str(e)}"))
            return

        created_count = 0
        updated_count = 0

        # Run within transactional bounds to guarantee atomicity
        from django.db import transaction
        with transaction.atomic():
            for entry in entries:
                # Deduplicate based on unique question text
                obj, created = KnowledgeBase.objects.update_or_create(
                    question=entry['question'],
                    defaults={
                        'title': entry['title'],
                        'category': entry['category'],
                        'answer': entry['answer'],
                        'keywords': entry['keywords'],
                        'synonyms': entry.get('synonyms', ''),
                        'priority': entry.get('priority', 0),
                        'difficulty': entry.get('difficulty', 'Medium'),
                        'tags': entry.get('tags', ''),
                        'is_active': entry.get('is_active', True)
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed seeding. Created: {created_count}, Updated: {updated_count}. "
                f"Total entries in DB: {KnowledgeBase.objects.count()}"
            )
        )
