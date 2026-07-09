# Plan Categories
PLAN_FREE = 'Free'
PLAN_PRO = 'Pro'
PLAN_ENTERPRISE = 'Enterprise'

PLAN_CHOICES = [
    (PLAN_FREE, 'Free'),
    (PLAN_PRO, 'Pro'),
    (PLAN_ENTERPRISE, 'Enterprise'),
]

# Billing Intervals
INTERVAL_MONTHLY = 'Monthly'
INTERVAL_YEARLY = 'Yearly'

INTERVAL_CHOICES = [
    (INTERVAL_MONTHLY, 'Monthly'),
    (INTERVAL_YEARLY, 'Yearly'),
]

# Subscription Statuses
SUB_ACTIVE = 'Active'
SUB_TRIAL = 'Trial'
SUB_EXPIRED = 'Expired'
SUB_CANCELED = 'Canceled'

SUB_STATUS_CHOICES = [
    (SUB_ACTIVE, 'Active'),
    (SUB_TRIAL, 'Trial'),
    (SUB_EXPIRED, 'Expired'),
    (SUB_CANCELED, 'Canceled'),
]

# Payment Statuses
TXN_SUCCEEDED = 'Succeeded'
TXN_FAILED = 'Failed'
TXN_PENDING = 'Pending'

TXN_STATUS_CHOICES = [
    (TXN_SUCCEEDED, 'Succeeded'),
    (TXN_FAILED, 'Failed'),
    (TXN_PENDING, 'Pending'),
]
