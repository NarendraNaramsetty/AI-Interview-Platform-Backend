from django.db import models
from django.conf import settings
import uuid

class AdminSetting(models.Model):
    """
    Dynamically configurable system parameters (e.g. SMTP keys, API configurations, Gemini key, etc.).
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class AdminLog(models.Model):
    """
    Internal logs mapping system, authentication, and API exceptions/requests.
    """
    LOG_TYPES = (
        ('Authentication', 'Authentication'),
        ('API', 'API'),
        ('Error', 'Error'),
    )
    log_type = models.CharField(max_length=50, choices=LOG_TYPES, default='API')
    message = models.TextField()
    latency_ms = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_logs'
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.log_type}] {self.message[:50]} at {self.timestamp}"


class FAQ(models.Model):
    """
    Frequently Asked Questions content model.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question = models.TextField()
    answer = models.TextField()
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'question']

    def __str__(self):
        return self.question[:50]


class ContactMessage(models.Model):
    """
    Support inquiries from users or landing page contact forms.
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    reply_message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.email} ({self.status})"


class BugReport(models.Model):
    """
    Bug tickets filed by candidate users.
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=50, default='Medium') # Low, Medium, High, Critical
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bug_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - Severity: {self.severity} ({self.status})"
