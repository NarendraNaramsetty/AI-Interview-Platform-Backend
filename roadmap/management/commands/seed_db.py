from django.core.management.base import BaseCommand
from django.db import transaction
from questions.models import QuestionCategory, Company, JobRole, Topic, InterviewQuestion
from coding.models import CodingCategory, CodingProblem, TestCase
from roadmap.models import CareerPath, Roadmap, RoadmapModule, LearningResource

class Command(BaseCommand):
    help = 'Seeds the database with initial setup data for testing and integration.'

    def handle(self, *args, **options):
        self.stdout.write('Starting database seeding...')

        with transaction.atomic():
            # 1. Question Categories
            fe_cat, _ = QuestionCategory.objects.get_or_create(
                name='Frontend',
                defaults={'description': 'Frontend Web Development frameworks and libraries.', 'icon': 'layout', 'display_order': 1}
            )
            be_cat, _ = QuestionCategory.objects.get_or_create(
                name='Backend',
                defaults={'description': 'Backend server execution, APIs, and databases.', 'icon': 'server', 'display_order': 2}
            )
            sd_cat, _ = QuestionCategory.objects.get_or_create(
                name='System Design',
                defaults={'description': 'High-level architecture, scalability, and system layout.', 'icon': 'git-branch', 'display_order': 3}
            )
            bh_cat, _ = QuestionCategory.objects.get_or_create(
                name='Behavioral',
                defaults={'description': 'Communication, teamwork, and cultural alignment.', 'icon': 'users', 'display_order': 4}
            )

            # 2. Companies
            google, _ = Company.objects.get_or_create(name='Google', defaults={'website': 'https://google.com'})
            meta, _ = Company.objects.get_or_create(name='Meta', defaults={'website': 'https://meta.com'})
            amazon, _ = Company.objects.get_or_create(name='Amazon', defaults={'website': 'https://amazon.com'})
            stripe, _ = Company.objects.get_or_create(name='Stripe', defaults={'website': 'https://stripe.com'})

            # 3. Job Roles
            fe_role, _ = JobRole.objects.get_or_create(
                title='Frontend Engineer',
                experience_level='Any',
                defaults={
                    'category': fe_cat,
                    'description': 'React, JavaScript, Vite, Tailwind CSS, HTML, CSS'
                }
            )
            be_role, _ = JobRole.objects.get_or_create(
                title='Backend Engineer',
                experience_level='Any',
                defaults={
                    'category': be_cat,
                    'description': 'Python, Django, PostgreSQL, Redis, Docker, REST API'
                }
            )
            fs_role, _ = JobRole.objects.get_or_create(
                title='Full Stack Engineer',
                experience_level='Any',
                defaults={
                    'category': fe_cat,
                    'description': 'React, Node, Express, Python, Django, SQL'
                }
            )
            pm_role, _ = JobRole.objects.get_or_create(
                title='Product Manager',
                experience_level='Any',
                defaults={
                    'category': bh_cat,
                    'description': 'Agile, Scrum, Communication, Leadership, Jira'
                }
            )

            # 4. Topics
            react_topic, _ = Topic.objects.get_or_create(category=fe_cat, name='React.js', defaults={'description': 'Core components and hooks.'})
            django_topic, _ = Topic.objects.get_or_create(category=be_cat, name='Django', defaults={'description': 'REST frameworks and models.'})
            sql_topic, _ = Topic.objects.get_or_create(category=be_cat, name='SQL', defaults={'description': 'Query optimization.'})
            behavioral_topic, _ = Topic.objects.get_or_create(category=bh_cat, name='Behavioral Core', defaults={'description': 'STAR methodology.'})

            # 5. Coding Categories
            algo_coding_cat, _ = CodingCategory.objects.get_or_create(
                name='Algorithms',
                defaults={'description': 'Problem solving and algorithms.', 'display_order': 1}
            )
            db_coding_cat, _ = CodingCategory.objects.get_or_create(
                name='Databases',
                defaults={'description': 'SQL coding challenges.', 'display_order': 2}
            )

            # 6. Coding Problems
            two_sum, ts_created = CodingProblem.objects.get_or_create(
                title='Two Sum',
                defaults={
                    'problem_statement': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.',
                    'description': 'Classic hash map search challenge.',
                    'input_format': 'nums = [2,7,11,15], target = 9',
                    'output_format': '[0,1]',
                    'constraints': '2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9',
                    'sample_input': 'nums = [2,7,11,15], target = 9',
                    'sample_output': '[0,1]',
                    'explanation': 'Because nums[0] + nums[1] == 9, we return [0, 1].',
                    'difficulty': 'Easy',
                    'category': algo_coding_cat,
                    'company': google,
                    'tags': ['hashmap', 'arrays'],
                    'points': 10
                }
            )
            if ts_created:
                TestCase.objects.create(problem=two_sum, input_data='[2,7,11,15]\n9', expected_output='[0,1]', is_sample=True, is_hidden=False)

            rev_int, ri_created = CodingProblem.objects.get_or_create(
                title='Reverse Integer',
                defaults={
                    'problem_statement': 'Given a signed 32-bit integer x, return x with its digits reversed. If reversing x causes the value to go outside the signed 32-bit integer range [-2^31, 2^31 - 1], then return 0.',
                    'description': 'Numeric digit manipulation math problem.',
                    'input_format': 'x = 123',
                    'output_format': '321',
                    'constraints': '-2^31 <= x <= 2^31 - 1',
                    'sample_input': 'x = 123',
                    'sample_output': '321',
                    'explanation': 'Digits reversed mapping.',
                    'difficulty': 'Medium',
                    'category': algo_coding_cat,
                    'company': meta,
                    'tags': ['math', 'integers'],
                    'points': 20
                }
            )
            if ri_created:
                TestCase.objects.create(problem=rev_int, input_data='123', expected_output='321', is_sample=True, is_hidden=False)

            # 7. Career Paths & Roadmaps
            fe_cp, _ = CareerPath.objects.get_or_create(
                name='Frontend Developer',
                defaults={'description': 'Step-by-step path to master modern frontend stacks.', 'icon': 'layout', 'estimated_duration': '6 months', 'difficulty': 'Medium'}
            )
            be_cp, _ = CareerPath.objects.get_or_create(
                name='Backend Developer',
                defaults={'description': 'Pathway to learn Django, databases, and microservices.', 'icon': 'server', 'estimated_duration': '6 months', 'difficulty': 'Medium'}
            )

            fe_roadmap, _ = Roadmap.objects.get_or_create(
                title='Frontend Roadmap',
                career_path=fe_cp,
                defaults={'description': 'Core HTML, CSS, JavaScript, React framework concepts, and optimization techniques.', 'estimated_duration': '120 hours', 'difficulty': 'Medium'}
            )
            be_roadmap, _ = Roadmap.objects.get_or_create(
                title='Backend Roadmap',
                career_path=be_cp,
                defaults={'description': 'Python base scripting, database indexing, API routing structures, and caching mechanisms.', 'estimated_duration': '150 hours', 'difficulty': 'Medium'}
            )

            # Roadmap Modules
            m1, _ = RoadmapModule.objects.get_or_create(
                roadmap=fe_roadmap,
                title='HTML5 & CSS3 Essentials',
                defaults={'description': 'Semantic markup, layout paradigms (Flexbox, Grid), and responsive design.', 'module_order': 1, 'estimated_hours': 15, 'module_type': 'Core'}
            )
            m2, _ = RoadmapModule.objects.get_or_create(
                roadmap=fe_roadmap,
                title='Advanced Modern JavaScript',
                defaults={'description': 'Asynchronous programming, event loop mechanics, scoping closures, and ES6+ features.', 'module_order': 2, 'estimated_hours': 30, 'module_type': 'Core'}
            )

            m3, _ = RoadmapModule.objects.get_or_create(
                roadmap=be_roadmap,
                title='Python Programming Foundation',
                defaults={'description': 'Data structures, object-oriented concepts, and concurrency generators.', 'module_order': 1, 'estimated_hours': 20, 'module_type': 'Core'}
            )
            m4, _ = RoadmapModule.objects.get_or_create(
                roadmap=be_roadmap,
                title='Django REST Framework & PostgreSQL',
                defaults={'description': 'Database schemas creation, model relations, custom serializers, and SQL query indexing.', 'module_order': 2, 'estimated_hours': 40, 'module_type': 'Core'}
            )

            # Learning Resources
            LearningResource.objects.get_or_create(
                roadmap_module=m1,
                title='MDN Web Docs: HTML & CSS',
                defaults={'resource_type': 'Course', 'provider': 'Mozilla Developer Network', 'url': 'https://developer.mozilla.org', 'duration': 600, 'is_free': True}
            )
            LearningResource.objects.get_or_create(
                roadmap_module=m2,
                title='JavaScript Info tutorial',
                defaults={'resource_type': 'Book', 'provider': 'JavaScript.info', 'url': 'https://javascript.info', 'duration': 1200, 'is_free': True}
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))
