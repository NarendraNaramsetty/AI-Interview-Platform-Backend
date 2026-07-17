import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from questions.models import InterviewQuestion, QuestionCategory, Topic

print("=" * 60)
print("INTERVIEW QUESTION DATABASE ANALYSIS")
print("=" * 60)

total_questions = InterviewQuestion.objects.filter(is_active=True).count()
print(f"\n📊 Total Active Questions: {total_questions}")

print("\n" + "=" * 60)
print("QUESTIONS BY CATEGORY:")
print("=" * 60)
for cat in QuestionCategory.objects.filter(is_active=True).order_by('display_order'):
    count = InterviewQuestion.objects.filter(category=cat, is_active=True).count()
    print(f"  • {cat.name}: {count} questions")
    
    # Show topics under this category
    topics = Topic.objects.filter(category=cat)
    if topics.exists():
        for topic in topics:
            topic_count = InterviewQuestion.objects.filter(topic=topic, is_active=True).count()
            if topic_count > 0:
                print(f"    - {topic.name}: {topic_count} questions")

print("\n" + "=" * 60)
print("QUESTIONS BY DIFFICULTY:")
print("=" * 60)
difficulties = InterviewQuestion.objects.filter(is_active=True).values_list('difficulty', flat=True).distinct()
for diff in difficulties:
    count = InterviewQuestion.objects.filter(difficulty=diff, is_active=True).count()
    print(f"  • {diff}: {count} questions")

print("\n" + "=" * 60)
print("QUESTIONS BY ANSWER TYPE (Interview Mode):")
print("=" * 60)
answer_types = InterviewQuestion.objects.filter(is_active=True).values_list('answer_type', flat=True).distinct()
for ans_type in answer_types:
    count = InterviewQuestion.objects.filter(answer_type=ans_type, is_active=True).count()
    print(f"  • {ans_type}: {count} questions")

print("\n" + "=" * 60)
print("SAMPLE QUESTIONS (First 3):")
print("=" * 60)
for q in InterviewQuestion.objects.filter(is_active=True)[:3]:
    print(f"\n📝 {q.question[:80]}...")
    print(f"   Category: {q.category.name}")
    print(f"   Difficulty: {q.difficulty}")
    print(f"   Answer Type: {q.answer_type}")
    if q.topic:
        print(f"   Topic: {q.topic.name}")

print("\n" + "=" * 60)
