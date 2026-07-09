# Evaluation Statuses
STATUS_PENDING = 'Pending'
STATUS_PROCESSING = 'Processing'
STATUS_COMPLETED = 'Completed'
STATUS_FAILED = 'Failed'

EVALUATION_STATUS_CHOICES = [
    (STATUS_PENDING, 'Pending'),
    (STATUS_PROCESSING, 'Processing'),
    (STATUS_COMPLETED, 'Completed'),
    (STATUS_FAILED, 'Failed'),
]

# Overall Ratings
RATING_EXCELLENT = 'Excellent'
RATING_VERY_GOOD = 'Very Good'
RATING_GOOD = 'Good'
RATING_AVERAGE = 'Average'
RATING_NEEDS_IMPROVEMENT = 'Needs Improvement'

OVERALL_RATING_CHOICES = [
    (RATING_EXCELLENT, 'Excellent'),
    (RATING_VERY_GOOD, 'Very Good'),
    (RATING_GOOD, 'Good'),
    (RATING_AVERAGE, 'Average'),
    (RATING_NEEDS_IMPROVEMENT, 'Needs Improvement'),
]

# Suggestion Priorities
PRIORITY_LOW = 'Low'
PRIORITY_MEDIUM = 'Medium'
PRIORITY_HIGH = 'High'
PRIORITY_CRITICAL = 'Critical'

PRIORITY_CHOICES = [
    (PRIORITY_LOW, 'Low'),
    (PRIORITY_MEDIUM, 'Medium'),
    (PRIORITY_HIGH, 'High'),
    (PRIORITY_CRITICAL, 'Critical'),
]

# Recommended Resource Types
RESOURCE_YOUTUBE = 'YouTube'
RESOURCE_DOCUMENTATION = 'Documentation'
RESOURCE_ARTICLE = 'Article'
RESOURCE_COURSE = 'Course'
RESOURCE_BOOK = 'Book'
RESOURCE_PRACTICE_SET = 'Practice Set'

RESOURCE_TYPE_CHOICES = [
    (RESOURCE_YOUTUBE, 'YouTube'),
    (RESOURCE_DOCUMENTATION, 'Documentation'),
    (RESOURCE_ARTICLE, 'Article'),
    (RESOURCE_COURSE, 'Course'),
    (RESOURCE_BOOK, 'Book'),
    (RESOURCE_PRACTICE_SET, 'Practice Set'),
]
