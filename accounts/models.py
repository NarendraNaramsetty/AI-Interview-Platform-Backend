import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from .validators import (
    validate_phone_number,
    validate_profile_picture_file,
    validate_date_of_birth,
    validate_linkedin_url,
    validate_github_url
)

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email).lower().strip()
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})


    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User Model supporting UUIDs, unique emails as usernames,
    profiles, verification states, and OTP codes.
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    username = models.CharField(max_length=150, unique=False, null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    
    phone_number = models.CharField(max_length=15, blank=True, validators=[validate_phone_number])
    country = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        validators=[validate_profile_picture_file]
    )
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True, validators=[validate_date_of_birth])
    gender = models.CharField(max_length=20, blank=True)
    
    linkedin_url = models.URLField(blank=True, validators=[validate_linkedin_url])
    github_url = models.URLField(blank=True, validators=[validate_github_url])
    portfolio_url = models.URLField(blank=True)
    role = models.CharField(max_length=50, default='Developer')
    provider = models.CharField(max_length=50, default='local')
    
    is_verified = models.BooleanField(default=False)
    
    # OTP fields for password resets & verification
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
