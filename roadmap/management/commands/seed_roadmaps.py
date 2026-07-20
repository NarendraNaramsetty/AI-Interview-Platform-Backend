import os
import json
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from roadmap.models import CareerPath, Roadmap, RoadmapModule

class Command(BaseCommand):
    help = 'Seeds production-grade roadmaps for all 23 career roles idempotently.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'seed_data', 'roadmap_data.json'),
            help='Path to roadmap JSON seed file'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        file_path = os.path.abspath(options['file'])
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Seed file not found at {file_path}"))
            return

        self.stdout.write(f"Reading seed file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            roadmaps_data = json.load(f)

        total_roles = len(roadmaps_data)
        self.stdout.write(f"Found {total_roles} career roles in seed payload.")

        created_paths_count = 0
        created_roadmaps_count = 0
        created_modules_count = 0

        with transaction.atomic():
            for role_item in roadmaps_data:
                role_name = role_item.get('role')
                desc = role_item.get('description', '')
                duration = role_item.get('estimated_duration', '4-6 Months')
                difficulty = role_item.get('difficulty', 'Intermediate')
                modules_data = role_item.get('modules', [])

                # 1. Get or Create CareerPath
                career_path, cp_created = CareerPath.objects.get_or_create(
                    name=role_name,
                    defaults={
                        'description': desc,
                        'estimated_duration': duration,
                        'difficulty': difficulty,
                        'is_active': True
                    }
                )
                if cp_created:
                    created_paths_count += 1

                # 2. Get or Create Roadmap Template
                roadmap_title = f"{role_name} Roadmap"
                roadmap, rm_created = Roadmap.objects.get_or_create(
                    career_path=career_path,
                    title=roadmap_title,
                    defaults={
                        'description': desc,
                        'estimated_duration': duration,
                        'difficulty': difficulty,
                        'total_modules': len(modules_data),
                        'is_active': True
                    }
                )
                if rm_created:
                    created_roadmaps_count += 1

                # 3. Pre-fetch existing modules for this roadmap
                existing_module_keys = set(
                    RoadmapModule.objects.filter(roadmap=roadmap).values_list('title', 'module_order')
                )

                modules_to_create = []
                for m_idx, m in enumerate(modules_data, start=1):
                    m_title = m.get('title')
                    m_order = m.get('module_order', m_idx)
                    m_desc = m.get('description', '')
                    m_hours = m.get('estimated_hours', 15)
                    m_diff = m.get('difficulty', 'Medium')
                    m_topics = m.get('key_topics', [])
                    m_prereqs = m.get('prerequisites', 'None')

                    # Build key topics into description text if needed
                    full_desc = m_desc
                    if m_topics:
                        full_desc += f"\n\nKey Topics: {', '.join(m_topics)}"

                    if (m_title, m_order) not in existing_module_keys:
                        modules_to_create.append(
                            RoadmapModule(
                                roadmap=roadmap,
                                title=m_title,
                                description=full_desc,
                                module_order=m_order,
                                estimated_hours=m_hours,
                                difficulty=m_diff,
                                prerequisites=m_prereqs
                            )
                        )

                if modules_to_create:
                    RoadmapModule.objects.bulk_create(
                        modules_to_create,
                        batch_size=500,
                        ignore_conflicts=True
                    )
                    created_modules_count += len(modules_to_create)

                # Update total modules count
                actual_module_count = RoadmapModule.objects.filter(roadmap=roadmap).count()
                if roadmap.total_modules != actual_module_count:
                    roadmap.total_modules = actual_module_count
                    roadmap.save(update_fields=['total_modules'])

        elapsed = round(time.time() - start_time, 2)
        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded roadmaps!\n"
            f"  - Career Paths: {CareerPath.objects.count()} (New: {created_paths_count})\n"
            f"  - Roadmaps: {Roadmap.objects.count()} (New: {created_roadmaps_count})\n"
            f"  - Modules: {RoadmapModule.objects.count()} (New: {created_modules_count})\n"
            f"  - Execution Time: {elapsed} seconds"
        ))
