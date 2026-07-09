# Difficulties Choices
DIFFICULTY_EASY = 'Easy'
DIFFICULTY_MEDIUM = 'Medium'
DIFFICULTY_HARD = 'Hard'

DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, 'Easy'),
    (DIFFICULTY_MEDIUM, 'Medium'),
    (DIFFICULTY_HARD, 'Hard'),
]

# Interview Type Choices
INTERVIEW_TYPE_HR = 'HR'
INTERVIEW_TYPE_TECHNICAL = 'Technical'
INTERVIEW_TYPE_CODING = 'Coding'
INTERVIEW_TYPE_MIXED = 'Mixed'
INTERVIEW_TYPE_CUSTOM = 'Custom'

INTERVIEW_TYPE_CHOICES = [
    (INTERVIEW_TYPE_HR, 'HR'),
    (INTERVIEW_TYPE_TECHNICAL, 'Technical'),
    (INTERVIEW_TYPE_CODING, 'Coding'),
    (INTERVIEW_TYPE_MIXED, 'Mixed'),
    (INTERVIEW_TYPE_CUSTOM, 'Custom'),
]

# Mode Choices
MODE_TEXT = 'Text'
MODE_VOICE = 'Voice'

MODE_CHOICES = [
    (MODE_TEXT, 'Text'),
    (MODE_VOICE, 'Voice'),
]

# Session Status Choices
STATUS_SCHEDULED = 'Scheduled'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_COMPLETED = 'Completed'
STATUS_CANCELLED = 'Cancelled'
STATUS_PAUSED = 'Paused'

STATUS_CHOICES = [
    (STATUS_SCHEDULED, 'Scheduled'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_COMPLETED, 'Completed'),
    (STATUS_CANCELLED, 'Cancelled'),
    (STATUS_PAUSED, 'Paused'),
]

# Question Source Choices
SOURCE_DATABASE = 'Database'
SOURCE_AI = 'AI'
SOURCE_MANUAL = 'Manual'

SOURCE_CHOICES = [
    (SOURCE_DATABASE, 'Database'),
    (SOURCE_AI, 'AI'),
    (SOURCE_MANUAL, 'Manual'),
]

# Answer Type Choices (matching modes)
ANSWER_TYPE_TEXT = 'Text'
ANSWER_TYPE_VOICE = 'Voice'

ANSWER_TYPE_CHOICES = [
    (ANSWER_TYPE_TEXT, 'Text'),
    (ANSWER_TYPE_VOICE, 'Voice'),
]
