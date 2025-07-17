from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile,PasswordResetOTP,EmailVerificationOTP

# Customizing how User appears in admin
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('id', 'email', 'username', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role Info', {'fields': ('role',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )

# Custom ProfileAdmin (optional but useful)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'fullname', 'phone_number', 'gender', 'date_of_birth')
    search_fields = ('user__email', 'fullname', 'phone_number')
    list_filter = ('gender',)

# Register both
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(PasswordResetOTP)
admin.site.register(EmailVerificationOTP)
