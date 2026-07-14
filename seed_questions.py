import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from questions.models import QuestionCategory, Topic, Company, JobRole, InterviewQuestion
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

# Create Categories
frontend_cat, _ = QuestionCategory.objects.get_or_create(name='Frontend Development', defaults={'icon': 'Monitor', 'display_order': 1})
backend_cat, _ = QuestionCategory.objects.get_or_create(name='Backend Development', defaults={'icon': 'Server', 'display_order': 2})
devops_cat, _ = QuestionCategory.objects.get_or_create(name='DevOps & Infrastructure', defaults={'icon': 'Cloud', 'display_order': 3})
behavioral_cat, _ = QuestionCategory.objects.get_or_create(name='Behavioral', defaults={'icon': 'User', 'display_order': 4})

# Create Topics
topics_data = {
    frontend_cat: [
        ('React Hooks & State', 'React component lifecycle, useState, useEffect, custom hooks.'),
        ('Virtual DOM & Performance', 'Reconciliation algorithm, key prop, React.memo, windowing.'),
        ('JavaScript Closures & Scope', 'Lexical scoping, memory leaks, closures, hoisting.'),
        ('CSS Layouts & Responsive Design', 'Flexbox, Grid, media queries, mobile-first design.')
    ],
    backend_cat: [
        ('Django ORM & Queries', 'N+1 queries, select_related, prefetch_related, indexing.'),
        ('REST API Design', 'HTTP methods, status codes, REST constraints, API versioning.'),
        ('Redis Caching Strategies', 'Cache aside, cache invalidation, key TTLs.'),
        ('Database SQL Optimization', 'Indexes, execution plans, joins, ACID properties.')
    ],
    devops_cat: [
        ('Docker Containers', 'Dockerfile layers, multi-stage builds, port mapping.'),
        ('CI/CD Pipelines', 'GitHub Actions, GitLab CI, pipeline stages, automated tests.')
    ],
    behavioral_cat: [
        ('STAR Method Situational', 'Situation, Task, Action, Result structured storytelling.'),
        ('Conflict Resolution', 'Handling technical disagreements or team conflicts.')
    ]
}

topics_map = {}
for cat, topics in topics_data.items():
    for name, desc in topics:
        t, _ = Topic.objects.get_or_create(category=cat, name=name, defaults={'description': desc})
        topics_map[name] = t

# Create Job Roles
roles_data = [
    ('Frontend Engineer', 'Any', frontend_cat),
    ('Backend Engineer', 'Any', backend_cat),
    ('Full Stack Engineer', 'Any', backend_cat),
    ('Product Manager', 'Any', behavioral_cat)
]
for title, level, cat in roles_data:
    JobRole.objects.get_or_create(title=title, experience_level=level, defaults={'category': cat})

# Create Companies
companies_names = ['Google', 'Amazon', 'Microsoft', 'Meta', 'Netflix']
companies_map = {}
for c_name in companies_names:
    c, _ = Company.objects.get_or_create(name=c_name, defaults={'website': f'https://{c_name.lower()}.com'})
    companies_map[c_name] = c

# High quality interview questions data (One question for every single topic)
questions_data = [
    # Frontend Development
    {
        'question': 'Can you explain the difference between useEffect and useLayoutEffect in React, and when you should use each?',
        'short_description': 'React hook useEffect vs useLayoutEffect',
        'category': frontend_cat,
        'topic_name': 'React Hooks & State',
        'company_name': 'Meta',
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['React', 'Hooks', 'Rendering'],
        'hints': ['useEffect runs asynchronously after paint.', 'useLayoutEffect runs synchronously before paint.', 'useLayoutEffect can block rendering.'],
        'expected_answer': 'useEffect runs asynchronously after the DOM paint. useLayoutEffect runs synchronously after DOM mutations but before paint, suitable for DOM measurements or layout styling adjustments to prevent flickering.',
        'explanation': 'useEffect is standard for side effects. useLayoutEffect blocks browser painting, so use it sparingly.'
    },
    {
        'question': 'What is a JavaScript closure? Can you write a simple counter function that demonstrates closure and encapsulates state?',
        'short_description': 'JS closures and state encapsulation',
        'category': frontend_cat,
        'topic_name': 'JavaScript Closures & Scope',
        'company_name': 'Google',
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['JavaScript', 'Closures', 'Scope'],
        'hints': ['A closure remembers its lexical environment.', 'Return a function that accesses an outer variable.'],
        'expected_answer': 'A closure is the combination of a function bundled together with references to its surrounding state (lexical environment). It allows an inner function to access variables of its outer function even after the outer function has returned.',
        'explanation': 'Closures are used for data privacy and modular design patterns.'
    },
    {
        'question': 'What is the difference between CSS Grid and Flexbox? When should you use one layout model over the other?',
        'short_description': 'CSS Grid vs Flexbox layout models',
        'category': frontend_cat,
        'topic_name': 'CSS Layouts & Responsive Design',
        'company_name': 'Microsoft',
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['CSS', 'Flexbox', 'Grid', 'Layout'],
        'hints': ['Flexbox is one-dimensional (row or column).', 'Grid is two-dimensional (rows and columns).', 'Flexbox is content-focused; Grid is layout-focused.'],
        'expected_answer': 'Flexbox is a one-dimensional layout model (dealing with rows OR columns), content-focused, ideal for aligning items inside a header or list. CSS Grid is a two-dimensional layout model (rows AND columns), structure-focused, designed for building full-page layouts or dynamic dashboard matrices.',
        'explanation': 'Combine both models: use Grid for page layout structure, and Flexbox for aligning components within Grid cells.'
    },
    {
        'question': 'How does React\'s Virtual DOM reconciliation algorithm work, and why is the "key" prop critical when rendering dynamic lists?',
        'short_description': 'React Virtual DOM and reconciliation key prop',
        'category': frontend_cat,
        'topic_name': 'Virtual DOM & Performance',
        'company_name': 'Meta',
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['React', 'Virtual DOM', 'Reconciliation', 'Performance'],
        'hints': ['Reconciliation compares the new Virtual DOM with the old one.', 'Keys help React identify which items changed, were added, or were removed.', 'Avoid using array index as keys for lists that can reorder.'],
        'expected_answer': 'React reconciliation compares virtual representation structures using a diffing algorithm (O(N) time complexity). The key prop provides a stable identity, allowing React to match dynamic components across renders, preventing wasteful re-renderings and state loss.',
        'explanation': 'Providing unique stable keys is critical for avoiding rendering errors and preserving component-internal state.'
    },
    
    # Backend Development
    {
        'question': 'What is the N+1 queries problem in relational databases, and how do you diagnose and resolve it when using Django ORM?',
        'short_description': 'N+1 queries in Django ORM',
        'category': backend_cat,
        'topic_name': 'Django ORM & Queries',
        'company_name': 'Amazon',
        'difficulty': 'Medium',
        'expected_duration': 6,
        'answer_type': 'Text',
        'tags': ['Django', 'ORM', 'Databases', 'Performance'],
        'hints': ['N+1 happens when loading related records in a loop.', 'Use select_related for foreign keys.', 'Use prefetch_related for many-to-many.'],
        'expected_answer': 'N+1 queries happen when the ORM executes one initial query to fetch N records, and then makes N additional queries to fetch related items. In Django, resolve it using select_related() (SQL JOIN) for foreign key relations and prefetch_related() (separate query with IN lookup) for multi-valued relations.',
        'explanation': 'Use django-debug-toolbar or database query logging to detect N+1 queries.'
    },
    {
        'question': 'How does Redis cache-aside strategy work, and what are the strategies for handling cache invalidation to prevent stale data?',
        'short_description': 'Redis Cache-Aside and Invalidation',
        'category': backend_cat,
        'topic_name': 'Redis Caching Strategies',
        'company_name': 'Netflix',
        'difficulty': 'Hard',
        'expected_duration': 8,
        'answer_type': 'Text',
        'tags': ['Redis', 'Caching', 'Architecture'],
        'hints': ['Cache-aside reads from cache first, then DB.', 'Write to DB and delete from cache.', 'Use Time to Live (TTL) as a fallback.'],
        'expected_answer': 'In cache-aside, the application queries the cache first. On a cache miss, it reads from the DB, stores the result in the cache, and returns it. Invalidation is handled by deleting the cache key when the database is updated (Write-Through/Delete-on-Update) or by configuring TTL (Time To Live).',
        'explanation': 'Cache invalidation is one of the hardest problems in computer science.'
    },
    {
        'question': 'Can you describe the core constraints of REST API design? Also, explain appropriate use cases for standard HTTP status codes.',
        'short_description': 'REST API constraints and HTTP status codes',
        'category': backend_cat,
        'topic_name': 'REST API Design',
        'company_name': 'Google',
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['APIs', 'REST', 'HTTP'],
        'hints': ['Statelessness, Client-Server separation, Uniform Interface.', '200 is OK, 201 is Created, 400 is Bad Request.', '401 is Unauthorized, 403 is Forbidden, 500 is Internal Server Error.'],
        'expected_answer': 'REST constraints include Client-Server, Statelessness, Cacheability, Layered System, and Uniform Interface. HTTP status codes designate query outcomes: 200 (OK), 201 (Created), 400 (Client validation error), 401 (Authentication required), 403 (Permission forbidden), 404 (Resource missing), and 500 (Server exception).',
        'explanation': 'Adhering to correct HTTP semantics is vital for public API client integrations.'
    },
    {
        'question': 'What is the difference between clustered and non-clustered indexes in SQL databases? How do database writes affect index maintenance?',
        'short_description': 'Clustered vs Non-clustered SQL Indexes',
        'category': backend_cat,
        'topic_name': 'Database SQL Optimization',
        'company_name': 'Amazon',
        'difficulty': 'Hard',
        'expected_duration': 6,
        'answer_type': 'Text',
        'tags': ['SQL', 'Indexing', 'Databases', 'Optimization'],
        'hints': ['Clustered indexes define the physical storage order of table data.', 'Non-clustered indexes contain pointers to the physical data rows.', 'Indices speed up reads but slow down inserts, updates, and deletes.'],
        'expected_answer': 'A clustered index determines the physical order of data storage in a database table (one per table). A non-clustered index is stored in a separate structure containing pointers to the data rows. Writes are slowed down by indexes because the database must update the index b-tree structures for every insert/update/delete operation.',
        'explanation': 'Analyze read/write ratios before applying multiple non-clustered indexes on write-heavy tables.'
    },
    
    # DevOps & Infrastructure
    {
        'question': 'What are Docker multi-stage builds, and why are they considered a best practice for containerizing applications?',
        'short_description': 'Docker multi-stage builds',
        'category': devops_cat,
        'topic_name': 'Docker Containers',
        'company_name': 'Microsoft',
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Docker', 'DevOps', 'Containers'],
        'hints': ['Multi-stage uses multiple FROM instructions.', 'It allows copying build artifacts between stages.', 'It keeps the final production image small.'],
        'expected_answer': 'Docker multi-stage builds allow developers to use multiple FROM statements in a single Dockerfile. You can compile artifacts in a build stage containing SDKs and compilers, then copy only the compiled binaries into a lightweight runtime image, significantly reducing final image size and vulnerability surface area.',
        'explanation': 'This keeps the production image extremely small and secure by excluding build tools.'
    },
    {
        'question': 'What are CI/CD pipelines, and what are the typical stages involved in automated deployment flows?',
        'short_description': 'CI/CD deployment pipeline stages',
        'category': devops_cat,
        'topic_name': 'CI/CD Pipelines',
        'company_name': 'Google',
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['CI/CD', 'DevOps', 'Pipelines'],
        'hints': ['Continuous Integration focuses on compilation and testing.', 'Continuous Deployment focuses on packaging and releasing.', 'Stages include Build, Test, Package, Release.'],
        'expected_answer': 'CI/CD stands for Continuous Integration (merging developer branches, compiling, and running automated tests) and Continuous Delivery/Deployment (automatically releasing tested Docker containers or artifact versions to staging/production environments). Key stages: Checkout, Lint, Unit Test, Build Image, Integration Test, Deploy.',
        'explanation': 'Pipelines ensure reliable, reproducible release cycles and prevent broken updates in production.'
    },
    
    # Behavioral
    {
        'question': 'Describe a time when you encountered a major roadblock or critical production bug close to a release deadline. How did you handle it using the STAR method?',
        'short_description': 'Dealing with roadblock/critical bug',
        'category': behavioral_cat,
        'topic_name': 'STAR Method Situational',
        'company_name': 'Google',
        'difficulty': 'Easy',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Behavioral', 'STAR Method', 'Soft Skills'],
        'hints': ['Structure answer as Situation, Task, Action, Result.', 'Focus on your personal actions and outcomes.'],
        'expected_answer': 'Candidate should outline: Situation (a production-blocking issue before release), Task (need to quickly locate root cause and hotfix), Action (coordinated rollback, isolated regression test, patched memory leak), and Result (released on time with 99.9% uptime).',
        'explanation': 'Evaluates ownership, quick thinking, and structured explanation.'
    },
    {
        'question': 'Tell me about a time you had a technical disagreement with a team member. How did you approach the conflict to achieve a productive outcome?',
        'short_description': 'Resolving team technical disagreement',
        'category': behavioral_cat,
        'topic_name': 'Conflict Resolution',
        'company_name': 'Amazon',
        'difficulty': 'Easy',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Behavioral', 'Conflict Resolution', 'Teamwork'],
        'hints': ['Avoid blaming language; emphasize communication.', 'Use data/metrics or build a quick prototype to compare options.', 'Focus on what was best for the product and the team.'],
        'expected_answer': 'Candidate should show: active listening to the colleague\'s proposal, mapping out comparison criteria (scalability, dev speed), creating a small proof-of-concept benchmark, and aligning on the path that minimized technical debt for the project.',
        'explanation': 'Assesses collaboration, emotional maturity, and evidence-based decision-making.'
    }
]

created_count = 0
for q_dict in questions_data:
    topic = topics_map.get(q_dict['topic_name'])
    company = companies_map.get(q_dict['company_name'])
    
    # Try to find corresponding JobRole
    if q_dict['category'] == frontend_cat:
        role = JobRole.objects.filter(title='Frontend Engineer').first()
    elif q_dict['category'] == backend_cat:
        role = JobRole.objects.filter(title='Backend Engineer').first()
    else:
        role = None

    q, created = InterviewQuestion.objects.get_or_create(
        question=q_dict['question'],
        category=q_dict['category'],
        defaults={
            'short_description': q_dict['short_description'],
            'topic': topic,
            'company': company,
            'role': role,
            'difficulty': q_dict['difficulty'],
            'expected_duration': q_dict['expected_duration'],
            'answer_type': q_dict['answer_type'],
            'tags': q_dict['tags'],
            'hints': q_dict['hints'],
            'expected_answer': q_dict['expected_answer'],
            'explanation': q_dict['explanation'],
            'created_by': admin_user
        }
    )
    if created:
        created_count += 1

print(f"Successfully seeded {created_count} high-quality interview questions into the question bank!")
