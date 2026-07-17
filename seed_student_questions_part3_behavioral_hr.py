"""
Student-Focused Interview Questions - Part 3: Behavioral & HR Questions  
For freshers and campus placement preparation - 30 questions total
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from questions.models import QuestionCategory, Topic, InterviewQuestion
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

# Create/Get Categories
behavioral_cat = QuestionCategory.objects.get(name='Behavioral')
hr_cat, _ = QuestionCategory.objects.get_or_create(name='HR', defaults={'icon': 'Users', 'display_order': 10})

# Create/Get Topics
behavioral_topics = {
    'STAR Method Situational': 'Situation, Task, Action, Result structured storytelling',
    'Conflict Resolution': 'Handling technical disagreements or team conflicts',
    'Leadership & Initiative': 'Taking charge and driving projects forward',
    'Problem Solving': 'Analytical thinking and creative solutions',
    'Adaptability': 'Handling change and learning new technologies'
}

hr_topics = {
    'Personal Background': 'Tell me about yourself, strengths, weaknesses',
    'Company & Role Fit': 'Why this company, role expectations, career goals', 
    'Campus Specific': 'Academic projects, internships, extracurriculars',
    'Work Preferences': 'Work environment, team dynamics, learning style'
}

topics_map = {}

# Create behavioral topics
for topic_name, desc in behavioral_topics.items():
    t, _ = Topic.objects.get_or_create(category=behavioral_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# Create HR topics  
for topic_name, desc in hr_topics.items():
    t, _ = Topic.objects.get_or_create(category=hr_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# ============================================================================
# BEHAVIORAL QUESTIONS (15 Questions) - STAR Method & Situational
# ============================================================================

behavioral_questions = [
    {
        'question': 'Tell me about a time when you had to learn a new technology or programming language quickly for a project. How did you approach it?',
        'short_description': 'Learning new technology quickly',
        'category': behavioral_cat,
        'topic': topics_map['Adaptability'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Learning', 'Adaptability', 'Technology'],
        'hints': ['Use STAR format', 'Mention specific resources used', 'Highlight learning strategy', 'Show results achieved'],
        'expected_answer': 'Use STAR method: Situation (project requiring new tech), Task (need to learn quickly), Action (online courses, documentation, practice projects, mentorship), Result (successfully delivered project, gained new skill). Show systematic learning approach and resourcefulness.',
        'explanation': 'Tests adaptability and learning ability - crucial for tech roles with rapidly changing technologies.'
    },
    {
        'question': 'Describe a challenging bug or technical problem you encountered in a project. How did you go about debugging it?',
        'short_description': 'Debugging challenging technical problem',
        'category': behavioral_cat,
        'topic': topics_map['Problem Solving'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Problem Solving', 'Debugging', 'Technical'],
        'hints': ['Describe systematic debugging approach', 'Mention tools used', 'Show persistence', 'Explain learning outcome'],
        'expected_answer': 'STAR format: Situation (specific bug description), Task (need to fix for deadline), Action (systematic debugging - logs, breakpoints, rubber duck debugging, seeking help), Result (bug fixed, preventive measures implemented). Demonstrate methodical problem-solving approach.',
        'explanation': 'Evaluates analytical thinking and persistence - core skills for software development roles.'
    },
    {
        'question': 'Tell me about a time when you disagreed with a team member about a technical approach. How did you handle the situation?',
        'short_description': 'Technical disagreement with team member',
        'category': behavioral_cat,
        'topic': topics_map['Conflict Resolution'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Conflict Resolution', 'Teamwork', 'Communication'],
        'hints': ['Show respect for different opinions', 'Mention data-driven decision making', 'Highlight collaboration', 'Focus on project outcome'],
        'expected_answer': 'STAR: Situation (technical disagreement), Task (reach consensus for project success), Action (listened actively, presented evidence, created prototype comparison, involved third party if needed), Result (best solution chosen, maintained relationship). Show diplomatic problem-solving.',
        'explanation': 'Tests collaboration skills and emotional intelligence in technical team environments.'
    },
    {
        'question': 'Describe a project where you took the initiative to improve something that wasn\'t assigned to you. What motivated you?',
        'short_description': 'Taking initiative beyond assigned work',
        'category': behavioral_cat,
        'topic': topics_map['Leadership & Initiative'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Initiative', 'Leadership', 'Self-motivation'],
        'hints': ['Show proactive thinking', 'Mention impact on team/project', 'Highlight problem identification', 'Demonstrate ownership mindset'],
        'expected_answer': 'STAR: Situation (inefficient process/missing feature), Task (improve team productivity), Action (analyzed problem, proposed solution, implemented improvement, documented changes), Result (measurable improvement, team adoption). Shows ownership and proactive mindset.',
        'explanation': 'Evaluates self-motivation and leadership potential - valuable for career growth.'
    },
    {
        'question': 'Tell me about a time when you failed at something. What did you learn from that experience?',
        'short_description': 'Learning from failure experience',
        'category': behavioral_cat,
        'topic': topics_map['Problem Solving'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Failure', 'Learning', 'Growth Mindset'],
        'hints': ['Be honest about the failure', 'Focus on lessons learned', 'Show how you applied learnings', 'Demonstrate resilience'],
        'expected_answer': 'STAR: Situation (specific failure), Task (what was expected), Action (analyze what went wrong, identify improvements, implement changes), Result (better performance in future, new skills gained). Show growth mindset and self-reflection.',
        'explanation': 'Tests self-awareness, resilience, and ability to learn from mistakes - important for continuous improvement.'
    },
    {
        'question': 'Describe a situation where you had to work under a tight deadline. How did you manage your time and deliver results?',
        'short_description': 'Managing tight deadlines effectively',
        'category': behavioral_cat,
        'topic': topics_map['Problem Solving'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Time Management', 'Pressure', 'Prioritization'],
        'hints': ['Mention prioritization strategy', 'Show task breakdown', 'Highlight communication with stakeholders', 'Demonstrate results delivery'],
        'expected_answer': 'STAR: Situation (tight deadline project), Task (deliver quality work on time), Action (prioritized tasks, broke down work, eliminated non-essentials, communicated progress), Result (met deadline, maintained quality). Show time management and prioritization skills.',
        'explanation': 'Evaluates time management and performance under pressure - critical in fast-paced work environments.'
    },
    {
        'question': 'Tell me about a time when you received constructive criticism. How did you handle it and what did you do differently?',
        'short_description': 'Handling constructive criticism',
        'category': behavioral_cat,
        'topic': topics_map['Adaptability'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Feedback', 'Growth', 'Professional Development'],
        'hints': ['Show openness to feedback', 'Mention specific changes made', 'Highlight improvement achieved', 'Demonstrate coachability'],
        'expected_answer': 'STAR: Situation (received feedback), Task (improve performance), Action (listened actively, asked clarifying questions, created improvement plan, implemented changes), Result (better performance, stronger relationship with feedback giver). Show coachability and growth mindset.',
        'explanation': 'Tests coachability and openness to feedback - essential for professional growth and team dynamics.'
    },
    {
        'question': 'Describe a group project where you had to collaborate with people from different backgrounds or skill levels.',
        'short_description': 'Collaborating with diverse team members',
        'category': behavioral_cat,
        'topic': topics_map['Leadership & Initiative'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Teamwork', 'Diversity', 'Collaboration'],
        'hints': ['Show inclusive behavior', 'Mention how you leveraged different strengths', 'Highlight communication strategies', 'Focus on team success'],
        'expected_answer': 'STAR: Situation (diverse team project), Task (achieve common goal), Action (understood everyone\'s strengths, facilitated communication, created inclusive environment, leveraged diversity), Result (successful project, strong team bonds). Show inclusive leadership.',
        'explanation': 'Evaluates teamwork skills and ability to work in diverse, inclusive environments - increasingly important in modern workplaces.'
    },
    {
        'question': 'Tell me about a time when you had to explain a complex technical concept to someone without a technical background.',
        'short_description': 'Explaining technical concepts simply',
        'category': behavioral_cat,
        'topic': topics_map['Leadership & Initiative'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Communication', 'Technical Explanation', 'Simplification'],
        'hints': ['Use analogies and simple language', 'Mention checking for understanding', 'Show patience and empathy', 'Highlight successful outcome'],
        'expected_answer': 'STAR: Situation (need to explain technical concept), Task (ensure understanding), Action (used analogies, visual aids, simple language, checked understanding, answered questions patiently), Result (successful communication, project progress). Show communication skills.',
        'explanation': 'Tests communication skills and ability to bridge technical and non-technical stakeholders - valuable for career advancement.'
    },
    {
        'question': 'Describe a situation where you had to adapt to significant changes in a project or work environment.',
        'short_description': 'Adapting to significant changes',
        'category': behavioral_cat,
        'topic': topics_map['Adaptability'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Adaptability', 'Change Management', 'Flexibility'],
        'hints': ['Show positive attitude toward change', 'Mention specific adaptation strategies', 'Highlight learning opportunities', 'Focus on successful outcomes'],
        'expected_answer': 'STAR: Situation (significant change occurred), Task (adapt and maintain performance), Action (analyzed new requirements, updated skills, adjusted processes, maintained positive attitude), Result (successful adaptation, improved capabilities). Show flexibility and resilience.',
        'explanation': 'Evaluates adaptability and change management skills - crucial in dynamic tech industry.'
    },
    {
        'question': 'Tell me about a time when you went above and beyond what was expected in a project or role.',
        'short_description': 'Going above and beyond expectations',
        'category': behavioral_cat,
        'topic': topics_map['Leadership & Initiative'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Excellence', 'Initiative', 'Value Creation'],
        'hints': ['Show extra value delivered', 'Mention impact on stakeholders', 'Highlight personal motivation', 'Demonstrate ownership'],
        'expected_answer': 'STAR: Situation (project with specific requirements), Task (meet basic expectations), Action (identified additional opportunities, implemented extra features, improved quality beyond requirements), Result (exceeded expectations, positive recognition, enhanced project value). Show excellence mindset.',
        'explanation': 'Tests drive for excellence and value creation - qualities that lead to career success and promotions.'
    },
    {
        'question': 'Describe a situation where you had to learn from someone who was difficult to work with. How did you handle it?',
        'short_description': 'Learning from difficult colleagues',
        'category': behavioral_cat,
        'topic': topics_map['Conflict Resolution'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Difficult Relationships', 'Professional Growth', 'Patience'],
        'hints': ['Focus on learning opportunity', 'Show emotional maturity', 'Mention professional behavior maintained', 'Highlight knowledge gained'],
        'expected_answer': 'STAR: Situation (difficult colleague with valuable knowledge), Task (learn while maintaining professionalism), Action (focused on learning, separated personality from expertise, asked targeted questions, remained patient), Result (gained valuable knowledge, maintained professional relationship). Show maturity and learning focus.',
        'explanation': 'Tests emotional intelligence and ability to separate personal dynamics from professional growth opportunities.'
    },
    {
        'question': 'Tell me about a time when you identified a problem that others had missed. What did you do about it?',
        'short_description': 'Identifying overlooked problems',
        'category': behavioral_cat,
        'topic': topics_map['Problem Solving'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Problem Identification', 'Critical Thinking', 'Proactive'],
        'hints': ['Show analytical thinking', 'Mention how you raised the issue', 'Highlight solution approach', 'Demonstrate impact awareness'],
        'expected_answer': 'STAR: Situation (overlooked problem in system/process), Task (address potential issue), Action (analyzed thoroughly, documented findings, communicated diplomatically, proposed solutions), Result (problem prevented, system improved, recognition for foresight). Show critical thinking and proactive problem-solving.',
        'explanation': 'Evaluates critical thinking and proactive problem identification - valuable for preventing issues and improving systems.'
    },
    {
        'question': 'Describe a project where you had to coordinate with multiple stakeholders with different priorities.',
        'short_description': 'Coordinating multiple stakeholders',
        'category': behavioral_cat,
        'topic': topics_map['Leadership & Initiative'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Stakeholder Management', 'Coordination', 'Communication'],
        'hints': ['Show understanding of different perspectives', 'Mention communication strategies', 'Highlight compromise and alignment', 'Focus on project success'],
        'expected_answer': 'STAR: Situation (project with multiple stakeholders), Task (align different priorities), Action (understood each stakeholder\'s needs, facilitated discussions, found common ground, maintained regular communication), Result (successful project delivery, satisfied stakeholders). Show coordination and diplomacy skills.',
        'explanation': 'Tests stakeholder management and coordination abilities - important for project success in complex organizations.'
    },
    {
        'question': 'Tell me about a time when you had to make a decision with incomplete information. How did you approach it?',
        'short_description': 'Decision making with incomplete information',
        'category': behavioral_cat,
        'topic': topics_map['Problem Solving'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['STAR Method', 'Decision Making', 'Risk Assessment', 'Uncertainty'],
        'hints': ['Show structured decision-making process', 'Mention risk assessment', 'Highlight information gathering efforts', 'Demonstrate courage in uncertainty'],
        'expected_answer': 'STAR: Situation (decision required with limited info), Task (make best decision possible), Action (gathered available data, consulted experts, assessed risks, made informed decision, prepared contingency plans), Result (positive outcome, learned decision-making under uncertainty). Show structured thinking and courage.',
        'explanation': 'Evaluates decision-making skills under uncertainty - common in fast-paced business environments where perfect information is rare.'
    }
]

print("=" * 80)
print("SEEDING PART 3A: BEHAVIORAL QUESTIONS - 15 Questions")
print("=" * 80)

created_count = 0
for q_dict in behavioral_questions:
    q, created = InterviewQuestion.objects.get_or_create(
        question=q_dict['question'],
        category=q_dict['category'],
        defaults={
            'short_description': q_dict['short_description'],
            'topic': q_dict['topic'],
            'difficulty': q_dict['difficulty'],
            'expected_duration': q_dict['expected_duration'],
            'answer_type': q_dict['answer_type'],
            'tags': q_dict['tags'],
            'hints': q_dict['hints'],
            'expected_answer': q_dict['expected_answer'],
            'explanation': q_dict['explanation'],
            'created_by': admin_user,
            'source': 'Manual'
        }
    )
    if created:
        created_count += 1
        print(f"✓ Created: {q_dict['short_description']}")

print(f"\nBehavioral Questions: {len(behavioral_questions)} added")
# ============================================================================
# HR QUESTIONS (15 Questions) - Campus Placement & Entry-Level Focus
# ============================================================================

hr_questions = [
    {
        'question': 'Tell me about yourself. Walk me through your background and what brings you here today.',
        'short_description': 'Tell me about yourself',
        'category': hr_cat,
        'topic': topics_map['Personal Background'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Personal Introduction', 'Background', 'Career Summary'],
        'hints': ['Keep it professional and relevant', 'Follow past-present-future structure', 'Highlight key achievements', 'Connect to the role'],
        'expected_answer': 'Structure: Brief background (education/major), current situation (skills/projects), future goals (why this role/company). Keep concise (2-3 minutes), focus on relevant experiences, show enthusiasm. Example: CS graduate, worked on web dev projects, passionate about solving real-world problems, excited about this opportunity.',
        'explanation': 'Most common opening question - sets tone for entire interview and allows candidate to control first impression.'
    },
    {
        'question': 'Why are you interested in this company and this specific role?',
        'short_description': 'Why this company and role',
        'category': hr_cat,
        'topic': topics_map['Company & Role Fit'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Company Research', 'Role Alignment', 'Career Goals'],
        'hints': ['Show company research', 'Connect company values to personal values', 'Mention specific role responsibilities', 'Avoid generic answers'],
        'expected_answer': 'Demonstrate research about company mission, values, recent news, products. Connect your skills/interests to specific role requirements. Show genuine enthusiasm. Avoid: "good company to work for" - instead mention specific technologies, culture, growth opportunities, impact.',
        'explanation': 'Tests preparation, research skills, and genuine interest - helps employers identify committed candidates.'
    },
    {
        'question': 'What are your greatest strengths? Provide specific examples.',
        'short_description': 'Greatest strengths with examples',
        'category': hr_cat,
        'topic': topics_map['Personal Background'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Strengths', 'Self-Assessment', 'Examples'],
        'hints': ['Choose job-relevant strengths', 'Provide concrete examples', 'Show impact/results', 'Be authentic'],
        'expected_answer': 'Choose 2-3 relevant strengths (problem-solving, communication, learning agility). Support each with specific examples showing impact. For developers: "Strong debugging skills - found critical bug in group project that saved 2 days of rework" or "Quick learner - mastered React in 2 weeks for internship project."',
        'explanation': 'Evaluates self-awareness and ability to articulate value proposition with evidence.'
    },
    {
        'question': 'What would you consider your biggest weakness? How are you working to improve it?',
        'short_description': 'Biggest weakness and improvement',
        'category': hr_cat,
        'topic': topics_map['Personal Background'],
        'difficulty': 'Medium',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Weakness', 'Self-Improvement', 'Growth Mindset'],
        'hints': ['Choose real but improvable weakness', 'Show specific improvement efforts', 'Avoid cliché answers', 'Demonstrate self-awareness'],
        'expected_answer': 'Honest weakness that won\'t disqualify you, with concrete improvement plan. Good examples: "Initially struggled with public speaking - joined Toastmasters, now comfortable presenting" or "Perfectionist tendency slowed early projects - learned to set time limits and iterate." Avoid: "I work too hard."',
        'explanation': 'Tests self-awareness, honesty, and commitment to personal growth - shows coachability.'
    },
    {
        'question': 'Where do you see yourself in 5 years? What are your career goals?',
        'short_description': 'Career goals and 5-year vision',
        'category': hr_cat,
        'topic': topics_map['Company & Role Fit'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Career Goals', 'Future Vision', 'Ambition'],
        'hints': ['Show ambition but be realistic', 'Align with company growth paths', 'Mention skill development', 'Show long-term thinking'],
        'expected_answer': 'Realistic progression aligned with role/company. For entry-level: "Become proficient full-stack developer, lead small projects, mentor junior developers, possibly move into technical lead role. Continue learning new technologies and contribute to meaningful products." Show growth mindset and leadership potential.',
        'explanation': 'Assesses ambition, long-term thinking, and alignment with company career paths - helps predict retention.'
    },
    {
        'question': 'Tell me about your most significant college project. What role did you play and what did you learn?',
        'short_description': 'Most significant college project',
        'category': hr_cat,
        'topic': topics_map['Campus Specific'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['College Projects', 'Leadership', 'Technical Skills', 'Learning'],
        'hints': ['Choose technically relevant project', 'Highlight your specific contributions', 'Mention technologies used', 'Show learning outcomes'],
        'expected_answer': 'Describe project scope, your role, technologies used, challenges faced, solutions implemented, and results achieved. For group projects, emphasize your specific contributions. Connect learnings to job requirements. Example: e-commerce website with React/Node.js, led frontend development, learned API integration.',
        'explanation': 'Evaluates technical experience, project management, and ability to articulate technical work - key for entry-level roles.'
    },
    {
        'question': 'What programming languages and technologies are you most comfortable with? Which ones do you want to learn?',
        'short_description': 'Programming skills and learning interests',
        'category': hr_cat,
        'topic': topics_map['Campus Specific'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Technical Skills', 'Programming Languages', 'Learning Goals'],
        'hints': ['Be honest about skill levels', 'Mention recent projects', 'Show curiosity for learning', 'Align with job requirements'],
        'expected_answer': 'Honest assessment of proficiency levels. "Comfortable with Python, JavaScript, SQL from coursework and projects. Built web apps with React. Interested in learning cloud technologies like AWS, mobile development with React Native. Always eager to learn tools that solve real problems."',
        'explanation': 'Assesses current technical capabilities and learning mindset - important for matching role requirements and growth potential.'
    },
    {
        'question': 'Describe your internship experience. What did you accomplish and what challenges did you face?',
        'short_description': 'Internship experience and accomplishments',
        'category': hr_cat,
        'topic': topics_map['Campus Specific'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Voice',
        'tags': ['Internship', 'Professional Experience', 'Accomplishments', 'Challenges'],
        'hints': ['Focus on measurable accomplishments', 'Mention technologies and processes learned', 'Show professional growth', 'Highlight problem-solving'],
        'expected_answer': 'If no internship: mention relevant project work, freelance, or personal projects. If internship exists: describe role, projects completed, technologies learned, impact created, professional skills gained. "Interned at X, developed feature Y that improved user engagement by Z%, learned agile development, gained experience with production systems."',
        'explanation': 'Evaluates real-world experience and ability to create impact in professional environment.'
    },
    {
        'question': 'What extracurricular activities or leadership roles were you involved in during college?',
        'short_description': 'Extracurricular activities and leadership',
        'category': hr_cat,
        'topic': topics_map['Campus Specific'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Leadership', 'Extracurricular', 'Soft Skills', 'Team Building'],
        'hints': ['Highlight leadership and impact', 'Connect to professional skills', 'Show diverse interests', 'Mention achievements'],
        'expected_answer': 'Connect activities to professional skills. "President of coding club - organized hackathons, improved participation by 50%, developed leadership and event management skills. Volunteer tutor - enhanced communication and patience. These experiences taught me project management, team leadership, and public speaking."',
        'explanation': 'Assesses leadership potential, well-roundedness, and soft skills development outside academics.'
    },
    {
        'question': 'How do you handle stress and pressure, especially when learning new technologies quickly?',
        'short_description': 'Handling stress and pressure',
        'category': hr_cat,
        'topic': topics_map['Work Preferences'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Stress Management', 'Pressure', 'Learning Agility', 'Coping Strategies'],
        'hints': ['Show healthy coping mechanisms', 'Mention time management strategies', 'Give examples', 'Show resilience'],
        'expected_answer': 'Demonstrate healthy stress management: "I break complex problems into smaller tasks, prioritize based on deadlines, take regular breaks to maintain focus. During finals/project deadlines, I used time-blocking and Pomodoro technique. I also maintain work-life balance through exercise and hobbies."',
        'explanation': 'Evaluates resilience and stress management skills - important for handling demanding work environments.'
    },
    {
        'question': 'What type of work environment do you thrive in? Do you prefer working independently or in teams?',
        'short_description': 'Preferred work environment',
        'category': hr_cat,
        'topic': topics_map['Work Preferences'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Work Environment', 'Team Preferences', 'Work Style'],
        'hints': ['Show flexibility', 'Give examples from experience', 'Mention collaboration skills', 'Align with company culture'],
        'expected_answer': 'Show adaptability: "I enjoy both collaborative and independent work. Teams are great for brainstorming, code reviews, and learning from others. Independent work helps me focus on complex problems. In group projects, I contributed ideas and also completed individual tasks efficiently."',
        'explanation': 'Assesses cultural fit and work style compatibility with team dynamics and company environment.'
    },
    {
        'question': 'How do you stay updated with the latest technology trends and developments in software development?',
        'short_description': 'Staying updated with technology trends',
        'category': hr_cat,
        'topic': topics_map['Work Preferences'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Continuous Learning', 'Technology Trends', 'Professional Development'],
        'hints': ['Mention specific resources', 'Show active learning habit', 'Connect to practical application', 'Demonstrate curiosity'],
        'expected_answer': 'Show active learning: "I follow tech blogs like TechCrunch, Stack Overflow, GitHub trending. Subscribe to developer newsletters, watch YouTube channels like Traversy Media. Participate in online courses (Coursera, Udemy), attend virtual meetups, contribute to open-source projects. Recently learned about AI/ML trends and tried implementing basic ML models."',
        'explanation': 'Evaluates commitment to continuous learning - crucial for success in rapidly evolving tech industry.'
    },
    {
        'question': 'What salary range are you expecting for this position?',
        'short_description': 'Salary expectations',
        'category': hr_cat,
        'topic': topics_map['Company & Role Fit'],
        'difficulty': 'Medium',
        'expected_duration': 2,
        'answer_type': 'Voice',
        'tags': ['Salary', 'Compensation', 'Negotiation', 'Market Research'],
        'hints': ['Research market rates', 'Show flexibility', 'Focus on growth opportunity', 'Ask about total compensation'],
        'expected_answer': 'Show research: "Based on market research for entry-level positions in this location, I understand the range is X to Y. I\'m more focused on joining a company where I can grow and contribute meaningfully. I\'m open to discussing a fair compensation package including benefits and growth opportunities."',
        'explanation': 'Tests market awareness and negotiation approach - important for setting appropriate compensation expectations.'
    },
    {
        'question': 'Why should we hire you over other candidates?',
        'short_description': 'Why should we hire you',
        'category': hr_cat,
        'topic': topics_map['Personal Background'],
        'difficulty': 'Medium',
        'expected_duration': 3,
        'answer_type': 'Voice',
        'tags': ['Unique Value', 'Competitive Advantage', 'Self Marketing'],
        'hints': ['Highlight unique combination of skills', 'Show passion and motivation', 'Connect to company needs', 'Be confident but humble'],
        'expected_answer': 'Highlight unique combination: "My strong technical foundation in [relevant tech], combined with leadership experience from [specific example], and genuine passion for [company mission/products] makes me uniquely positioned to contribute immediately while growing with the team. I bring fresh perspective, eagerness to learn, and proven ability to deliver results."',
        'explanation': 'Tests ability to articulate unique value proposition and differentiate from other candidates.'
    },
    {
        'question': 'Do you have any questions for me about the role, team, or company?',
        'short_description': 'Questions about role/company',
        'category': hr_cat,
        'topic': topics_map['Company & Role Fit'],
        'difficulty': 'Easy',
        'expected_duration': 2,
        'answer_type': 'Voice',
        'tags': ['Questions for Interviewer', 'Company Research', 'Role Understanding'],
        'hints': ['Prepare thoughtful questions', 'Show genuine interest', 'Ask about growth and learning', 'Avoid salary/benefits initially'],
        'expected_answer': 'Good questions: "What does success look like in this role after 6 months?" "What\'s the team dynamic and collaboration style?" "What are the biggest technical challenges facing the team?" "How does the company support professional development?" "What do you enjoy most about working here?"',
        'explanation': 'Tests preparation, engagement, and genuine interest - also provides opportunity to evaluate company fit.'
    }
]

print("\n" + "=" * 80)
print("SEEDING PART 3B: HR QUESTIONS - 15 Questions")
print("=" * 80)

for q_dict in hr_questions:
    q, created = InterviewQuestion.objects.get_or_create(
        question=q_dict['question'],
        category=q_dict['category'],
        defaults={
            'short_description': q_dict['short_description'],
            'topic': q_dict['topic'],
            'difficulty': q_dict['difficulty'],
            'expected_duration': q_dict['expected_duration'],
            'answer_type': q_dict['answer_type'],
            'tags': q_dict['tags'],
            'hints': q_dict['hints'],
            'expected_answer': q_dict['expected_answer'],
            'explanation': q_dict['explanation'],
            'created_by': admin_user,
            'source': 'Manual'
        }
    )
    if created:
        created_count += 1
        print(f"✓ Created: {q_dict['short_description']}")

print(f"\nHR Questions: {len(hr_questions)} added")

print("\n" + "=" * 80)
print(f"PART 3 COMPLETE! Total Questions Created: {created_count}")
print("Breakdown:")
print(f"  • Behavioral Questions (STAR Method): 15 questions")
print(f"  • HR Questions (Campus Placement): 15 questions") 
print("=" * 80)