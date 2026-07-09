# Notification Types
NOTIF_SYSTEM = 'System'
# Future types
NOTIF_EMAIL = 'Email'
NOTIF_PUSH = 'Push'

NOTIFICATION_TYPE_CHOICES = [
    (NOTIF_SYSTEM, 'System'),
    (NOTIF_EMAIL, 'Email'),
    (NOTIF_PUSH, 'Push'),
]

# Frequency Settings Choices
FREQ_DAILY = 'Daily'
FREQ_WEEKLY = 'Weekly'
FREQ_INSTANT = 'Instant'

FREQUENCY_CHOICES = [
    (FREQ_DAILY, 'Daily'),
    (FREQ_WEEKLY, 'Weekly'),
    (FREQ_INSTANT, 'Instant'),
]
