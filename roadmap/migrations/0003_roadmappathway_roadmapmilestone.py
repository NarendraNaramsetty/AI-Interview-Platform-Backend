# Generated migration for RoadmapPathway and RoadmapMilestone models

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('roadmap', '0002_moduleprogress_coding_status_and_more'),  # Adjust based on your last migration
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RoadmapPathway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('user_interest_text', models.TextField(help_text='What user stated they want to become/learn (e.g., "QA Engineer")')),
                ('pathway_title', models.CharField(help_text='Generated title for the pathway', max_length=150)),
                ('inferred_starting_level', models.CharField(
                    choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')],
                    default='Beginner',
                    help_text='Auto-inferred from user input',
                    max_length=20
                )),
                ('inferred_level_reason', models.TextField(help_text='Why this starting level was chosen')),
                ('overall_readiness_estimate_percent', models.IntegerField(
                    default=0,
                    help_text='Estimated readiness % for the goal (0-100)',
                    validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_pathways', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Roadmap Pathway',
                'verbose_name_plural': 'Roadmap Pathways',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RoadmapMilestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('milestone_number', models.IntegerField(help_text='Sequential order (1, 2, 3, ...)')),
                ('title', models.CharField(help_text="e.g., 'Testing Fundamentals & Mindset'", max_length=150)),
                ('difficulty_tag', models.CharField(
                    choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')],
                    help_text='Difficulty level for this specific milestone',
                    max_length=20
                )),
                ('description', models.TextField(help_text='What the user will learn in this milestone')),
                ('why_it_matters', models.TextField(help_text='Real-world relevance and job readiness impact')),
                ('estimated_hours', models.IntegerField(help_text='Estimated hours needed (5-8 hrs/week pace)')),
                ('key_topics', models.JSONField(
                    default=list,
                    help_text='List of specific topics/concepts to cover'
                )),
                ('is_completed', models.BooleanField(
                    default=False,
                    help_text='Whether user marked this milestone complete'
                )),
                ('progress_percent', models.IntegerField(
                    default=0,
                    help_text='User\'s progress through this milestone (0-100%)',
                    validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pathway', models.ForeignKey(help_text='Parent pathway this milestone belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='roadmap.roadmappathway')),
            ],
            options={
                'verbose_name': 'Roadmap Milestone',
                'verbose_name_plural': 'Roadmap Milestones',
                'ordering': ['pathway', 'milestone_number'],
                'unique_together': {('pathway', 'milestone_number')},
            },
        ),
    ]
