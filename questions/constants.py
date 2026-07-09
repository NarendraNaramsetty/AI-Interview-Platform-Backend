# Difficulties Choices
DIFFICULTY_EASY = 'Easy'
DIFFICULTY_MEDIUM = 'Medium'
DIFFICULTY_HARD = 'Hard'

DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, 'Easy'),
    (DIFFICULTY_MEDIUM, 'Medium'),
    (DIFFICULTY_HARD, 'Hard'),
]

# Source Choices
SOURCE_MANUAL = 'Manual'
SOURCE_AI = 'AI'
SOURCE_CSV = 'CSV'
SOURCE_EXCEL = 'Excel'
SOURCE_SYSTEM = 'System'

SOURCE_CHOICES = [
    (SOURCE_MANUAL, 'Manual'),
    (SOURCE_AI, 'AI'),
    (SOURCE_CSV, 'CSV'),
    (SOURCE_EXCEL, 'Excel'),
    (SOURCE_SYSTEM, 'System'),
]

# Answer Type Choices
ANSWER_TYPE_TEXT = 'Text'
ANSWER_TYPE_VOICE = 'Voice'
ANSWER_TYPE_CODING = 'Coding'
ANSWER_TYPE_MIXED = 'Mixed'
ANSWER_TYPE_CHOICES = 'Choices'

ANSWER_TYPE_CHOICES_LIST = [
    (ANSWER_TYPE_TEXT, 'Text'),
    (ANSWER_TYPE_VOICE, 'Voice'),
    (ANSWER_TYPE_CODING, 'Coding'),
    (ANSWER_TYPE_MIXED, 'Mixed'),
    (ANSWER_TYPE_CHOICES, 'Choices'),
]
