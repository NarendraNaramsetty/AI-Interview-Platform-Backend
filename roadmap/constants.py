# Difficulty Levels
DIFFICULTY_EASY = 'Easy'
DIFFICULTY_MEDIUM = 'Medium'
DIFFICULTY_HARD = 'Hard'

DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, 'Easy'),
    (DIFFICULTY_MEDIUM, 'Medium'),
    (DIFFICULTY_HARD, 'Hard'),
]

# Roadmap Module Types
TYPE_VIDEO = 'Video'
TYPE_ARTICLE = 'Article'
TYPE_PRACTICE = 'Practice'
TYPE_INTERVIEW = 'Interview'
TYPE_CODING = 'Coding'
TYPE_QUIZ = 'Quiz'
TYPE_PROJECT = 'Project'

MODULE_TYPE_CHOICES = [
    (TYPE_VIDEO, 'Video'),
    (TYPE_ARTICLE, 'Article'),
    (TYPE_PRACTICE, 'Practice'),
    (TYPE_INTERVIEW, 'Interview'),
    (TYPE_CODING, 'Coding'),
    (TYPE_QUIZ, 'Quiz'),
    (TYPE_PROJECT, 'Project'),
]

# Resource Categories
RES_YOUTUBE = 'YouTube'
RES_DOCS = 'Documentation'
RES_COURSE = 'Course'
RES_ARTICLE = 'Article'
RES_BOOK = 'Book'
RES_GITHUB = 'GitHub'
RES_WEBSITE = 'Website'
RES_PRACTICE = 'Practice'

RESOURCE_TYPE_CHOICES = [
    (RES_YOUTUBE, 'YouTube'),
    (RES_DOCS, 'Documentation'),
    (RES_COURSE, 'Course'),
    (RES_ARTICLE, 'Article'),
    (RES_BOOK, 'Book'),
    (RES_GITHUB, 'GitHub'),
    (RES_WEBSITE, 'Website'),
    (RES_PRACTICE, 'Practice'),
]

# User Roadmap Statuses
STATUS_NOT_STARTED = 'Not Started'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_COMPLETED = 'Completed'
STATUS_PAUSED = 'Paused'

ROADMAP_STATUS_CHOICES = [
    (STATUS_NOT_STARTED, 'Not Started'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_COMPLETED, 'Completed'),
    (STATUS_PAUSED, 'Paused'),
]

# Reminders Frequencies
FREQ_DAILY = 'Daily'
FREQ_WEEKLY = 'Weekly'
FREQ_MONTHLY = 'Monthly'

REMINDER_FREQUENCY_CHOICES = [
    (FREQ_DAILY, 'Daily'),
    (FREQ_WEEKLY, 'Weekly'),
    (FREQ_MONTHLY, 'Monthly'),
]
