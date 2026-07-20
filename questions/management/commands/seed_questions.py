import os
import json
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from questions.models import QuestionCategory, Topic, InterviewQuestion

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Seeds interview questions, categories, and topics into Neon Postgres / DB "
        "from JSON fixture files using efficient bulk operations."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to a single JSON seed file to import.'
        )
        parser.add_argument(
            '--dir',
            type=str,
            help='Path to a folder containing JSON seed files to import.'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Batch size for bulk_create operations (default: 500).'
        )

    def handle(self, *args, **options):
        start_time = time.time()

        # 1. Safety Guard: Check user existence in DB
        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not admin_user:
            raise CommandError(
                "No user found in the database. Please run 'python manage.py createsuperuser' "
                "first before running seed commands."
            )

        file_arg = options.get('file')
        dir_arg = options.get('dir')
        batch_size = options.get('batch_size', 500)

        # Determine target JSON files
        files_to_process = []
        if file_arg:
            if not os.path.isfile(file_arg):
                raise CommandError(f"Specified file does not exist: {file_arg}")
            files_to_process.append(os.path.abspath(file_arg))
        elif dir_arg:
            if not os.path.isdir(dir_arg):
                raise CommandError(f"Specified directory does not exist: {dir_arg}")
            files_to_process = [
                os.path.join(dir_arg, f)
                for f in sorted(os.listdir(dir_arg))
                if f.endswith('.json')
            ]
            if not files_to_process:
                raise CommandError(f"No .json files found in directory: {dir_arg}")
        else:
            default_dir = os.path.join('questions', 'fixtures', 'seed_data')
            if os.path.isdir(default_dir):
                files_to_process = [
                    os.path.join(default_dir, f)
                    for f in sorted(os.listdir(default_dir))
                    if f.endswith('.json')
                ]
            else:
                raise CommandError(
                    "No --file or --dir argument provided and default directory "
                    f"'{default_dir}' was not found."
                )

        self.stdout.write(self.style.SUCCESS(f"Found {len(files_to_process)} JSON fixture file(s) to process.\n"))

        # Global Counters
        grand_stats = {
            'files_processed': 0,
            'cat_created': 0,
            'cat_skipped': 0,
            'topic_created': 0,
            'topic_skipped': 0,
            'q_created': 0,
            'q_skipped': 0,
        }

        # 2. Process Each File
        for file_path in files_to_process:
            filename = os.path.basename(file_path)
            self.stdout.write(self.style.MIGRATE_HEADING(f"Processing Fixture File: {filename}"))

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as err:
                raise CommandError(f"Failed to read/parse JSON file '{file_path}': {err}")

            categories_data = data.get('categories', [])
            topics_data = data.get('topics', [])
            questions_data = data.get('questions', [])

            with transaction.atomic():
                file_stats = {
                    'cat_created': 0,
                    'cat_skipped': 0,
                    'topic_created': 0,
                    'topic_skipped': 0,
                    'q_created': 0,
                    'q_skipped': 0,
                }

                # A. Categories (get_or_create)
                cat_map = {}
                for cat_item in categories_data:
                    cat_name = cat_item.get('name')
                    if not cat_name:
                        continue
                    cat, created = QuestionCategory.objects.get_or_create(
                        name=cat_name,
                        defaults={
                            'icon': cat_item.get('icon', ''),
                            'display_order': cat_item.get('display_order', 0),
                            'description': cat_item.get('description', ''),
                        }
                    )
                    cat_map[cat_name] = cat
                    if created:
                        file_stats['cat_created'] += 1
                    else:
                        file_stats['cat_skipped'] += 1

                # B. Topics (get_or_create)
                topic_map = {}
                for top_item in topics_data:
                    top_name = top_item.get('name')
                    cat_name = top_item.get('category')
                    if not top_name or not cat_name:
                        continue

                    if cat_name in cat_map:
                        parent_cat = cat_map[cat_name]
                    else:
                        try:
                            parent_cat = QuestionCategory.objects.get(name=cat_name)
                            cat_map[cat_name] = parent_cat
                        except QuestionCategory.DoesNotExist:
                            raise CommandError(
                                f"Validation Error in {filename}: Parent category '{cat_name}' "
                                f"for topic '{top_name}' does not exist."
                            )

                    topic, created = Topic.objects.get_or_create(
                        category=parent_cat,
                        name=top_name,
                        defaults={
                            'description': top_item.get('description', '')
                        }
                    )
                    topic_map[(cat_name, top_name)] = topic
                    if created:
                        file_stats['topic_created'] += 1
                    else:
                        file_stats['topic_skipped'] += 1

                # C. Validate Topics for all Questions
                for idx, q_item in enumerate(questions_data, start=1):
                    q_cat_name = q_item.get('category')
                    q_top_name = q_item.get('topic')
                    q_title = q_item.get('short_description') or f"Question #{idx}"

                    if q_top_name:
                        if (q_cat_name, q_top_name) not in topic_map:
                            top_exists = Topic.objects.filter(
                                category__name=q_cat_name,
                                name=q_top_name
                            ).exists()
                            if not top_exists:
                                raise CommandError(
                                    f"Validation Error in {filename}: Topic '{q_top_name}' "
                                    f"(Category: '{q_cat_name}') referenced by question "
                                    f"'{q_title}' does not exist."
                                )

                # D. High-Performance Bulk Creation for Questions
                # 1. Pre-fetch existing question texts per category into a set
                target_categories = set(q_item.get('category') for q_item in questions_data if q_item.get('category'))
                existing_question_texts = defaultdict_set = {}
                for cname in target_categories:
                    existing_question_texts[cname] = set(
                        InterviewQuestion.objects.filter(category__name=cname).values_list('question', flat=True)
                    )

                questions_to_create = []

                for idx, q_item in enumerate(questions_data, start=1):
                    q_text = q_item.get('question')
                    q_cat_name = q_item.get('category')
                    q_top_name = q_item.get('topic')

                    if not q_text or not q_cat_name:
                        continue

                    # Check for duplicate in DB or current batch
                    known_texts = existing_question_texts.get(q_cat_name, set())
                    if q_text in known_texts:
                        file_stats['q_skipped'] += 1
                        continue

                    # Mark text as seen to avoid intra-file duplicates
                    known_texts.add(q_text)

                    # Retrieve Category
                    if q_cat_name in cat_map:
                        q_cat = cat_map[q_cat_name]
                    else:
                        q_cat = QuestionCategory.objects.get(name=q_cat_name)
                        cat_map[q_cat_name] = q_cat

                    # Retrieve Topic
                    q_topic = None
                    if q_top_name:
                        if (q_cat_name, q_top_name) in topic_map:
                            q_topic = topic_map[(q_cat_name, q_top_name)]
                        else:
                            q_topic = Topic.objects.get(category=q_cat, name=q_top_name)
                            topic_map[(q_cat_name, q_top_name)] = q_topic

                    # Create Model Instance
                    q_obj = InterviewQuestion(
                        question=q_text,
                        category=q_cat,
                        topic=q_topic,
                        short_description=q_item.get('short_description', ''),
                        difficulty=q_item.get('difficulty', 'Easy'),
                        expected_duration=q_item.get('expected_duration', 5),
                        answer_type=q_item.get('answer_type', 'Text'),
                        tags=q_item.get('tags', []),
                        hints=q_item.get('hints', []),
                        expected_answer=q_item.get('expected_answer', ''),
                        explanation=q_item.get('explanation', ''),
                        created_by=admin_user,
                        source='Manual',
                    )
                    questions_to_create.append(q_obj)
                    file_stats['q_created'] += 1

                # Bulk insert in batches
                if questions_to_create:
                    InterviewQuestion.objects.bulk_create(
                        questions_to_create,
                        batch_size=batch_size,
                        ignore_conflicts=True
                    )

            # Accumulate file stats into grand stats
            grand_stats['files_processed'] += 1
            grand_stats['cat_created'] += file_stats['cat_created']
            grand_stats['cat_skipped'] += file_stats['cat_skipped']
            grand_stats['topic_created'] += file_stats['topic_created']
            grand_stats['topic_skipped'] += file_stats['topic_skipped']
            grand_stats['q_created'] += file_stats['q_created']
            grand_stats['q_skipped'] += file_stats['q_skipped']

            # Log Progress Per File
            self.stdout.write(
                f"  Summary for {filename}:\n"
                f"    Categories: {file_stats['cat_created']} created, {file_stats['cat_skipped']} skipped\n"
                f"    Topics:     {file_stats['topic_created']} created, {file_stats['topic_skipped']} skipped\n"
                f"    Questions:  {file_stats['q_created']} created, {file_stats['q_skipped']} skipped\n"
            )

        elapsed = time.time() - start_time

        # 3. Print Grand Total Summary Table
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(self.style.SUCCESS("GRAND TOTAL SEEDING SUMMARY (NEON POSTGRES OPTIMIZED)"))
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(
            f"  Files Processed: {grand_stats['files_processed']}\n"
            f"  Categories:      {grand_stats['cat_created']} created, {grand_stats['cat_skipped']} skipped\n"
            f"  Topics:          {grand_stats['topic_created']} created, {grand_stats['topic_skipped']} skipped\n"
            f"  Questions:       {grand_stats['q_created']} created, {grand_stats['q_skipped']} skipped\n"
            f"  Total Time:      {elapsed:.2f} seconds\n"
        )
        self.stdout.write(self.style.SUCCESS("Seeding completed successfully."))
