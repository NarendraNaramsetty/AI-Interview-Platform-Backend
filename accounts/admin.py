from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """
    Extends standard Django UserAdmin configuration to manage CustomUser profiles
    within the administration portal.
    """
    model = CustomUser
    
    # Grid list display configuration
    list_display = [
        'email', 'first_name', 'last_name', 'role', 
        'is_verified', 'is_active', 'is_staff', 
        'profile_picture_preview'
    ]
    
    # Filter panels
    list_filter = ['is_verified', 'is_active', 'is_staff', 'role', 'created_at']
    
    # Search properties
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    
    # Default order
    ordering = ['-created_at']

    # Override standard edit fieldsets
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'date_of_birth', 'gender')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('PrepAI Profile parameters'), {
            'fields': ('uuid', 'phone_number', 'country', 'profile_picture', 'bio', 'role'),
        }),
        (_('Professional Portfolios'), {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url'),
        }),
        (_('Authentication OTP metadata'), {
            'fields': ('otp_code', 'otp_created_at'),
        }),
    )
    
    readonly_fields = ['uuid', 'last_login', 'date_joined']

    def profile_picture_preview(self, obj):
        """
        Renders a small circular image tag previewing the uploaded avatar.
        """
        if obj.profile_picture:
            return mark_safe(
                f'<img src="{obj.profile_picture.url}" width="36" height="36" '
                f'style="border-radius: 50%; object-fit: cover; border: 1.5px solid #6366F1;" />'
            )
        return _("No Avatar")
        
    profile_picture_preview.short_description = _("Avatar Preview")

admin.site.register(CustomUser, CustomUserAdmin)
