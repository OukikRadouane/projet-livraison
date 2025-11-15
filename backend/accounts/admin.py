from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	fieldsets = DjangoUserAdmin.fieldsets + (
		("Role & Capacity", {"fields": ("role", "capacity_kg")}),
	)
	list_display = ("username", "email", "role", "capacity_kg", "is_active")
	list_filter = ("role", "is_active", "is_staff")
