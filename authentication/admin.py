from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AdminUser


@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):
	"""Admin configuration for the custom AdminUser model."""
	model = AdminUser
	list_display = (
		"username",
		"email",
		"is_staff",
		"is_superuser",
		"is_active",
		"last_login",
		"last_login_ip",
		"login_attempts",
	)
	list_filter = ("is_staff", "is_superuser", "is_active")
	search_fields = ("username", "email", "first_name", "last_name")
	ordering = ("username",)

	fieldsets = (
		(None, {"fields": ("username", "password")}),
		("Personal info", {"fields": ("first_name", "last_name", "email")}),
		(
			"Permissions",
			{"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions", "is_admin")},
		),
		("Important dates", {"fields": ("last_login", "date_joined", "locked_until")}),
		("Security/Meta", {"fields": ("last_login_ip", "login_attempts")}),
	)

	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser", "is_active"),
			},
		),
	)

