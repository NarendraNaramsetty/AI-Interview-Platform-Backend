# Conversation Types
CONV_GENERAL = 'General'
CONV_RESUME = 'Resume'
CONV_INTERVIEW = 'Interview'
CONV_CODING = 'Coding'
CONV_HR = 'HR'
CONV_ROADMAP = 'Roadmap'
CONV_CAREER = 'Career'

CONVERSATION_TYPE_CHOICES = [
    (CONV_GENERAL, 'General'),
    (CONV_RESUME, 'Resume'),
    (CONV_INTERVIEW, 'Interview'),
    (CONV_CODING, 'Coding'),
    (CONV_HR, 'HR'),
    (CONV_ROADMAP, 'Roadmap'),
    (CONV_CAREER, 'Career'),
]

# Session Lifecycle Statuses
STATUS_ACTIVE = 'Active'
STATUS_ARCHIVED = 'Archived'
STATUS_DELETED = 'Deleted'

SESSION_STATUS_CHOICES = [
    (STATUS_ACTIVE, 'Active'),
    (STATUS_ARCHIVED, 'Archived'),
    (STATUS_DELETED, 'Deleted'),
]

# Speakers
SENDER_USER = 'User'
SENDER_AI = 'AI'

SENDER_CHOICES = [
    (SENDER_USER, 'User'),
    (SENDER_AI, 'AI'),
]

# Message Types
MSG_TEXT = 'Text'

MESSAGE_TYPE_CHOICES = [
    (MSG_TEXT, 'Text'),
]
