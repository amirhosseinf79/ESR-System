from django.contrib import admin
from . import models


class ShiftColumn(admin.ModelAdmin):
    list_display = ('company', 'employee', 'enter_time', 'exit_time')
    list_filter = ('is_deleted', 'enter_time', )

    def company(self, obj):
        return f"{obj.employee.company}"


class EmployeeColumn(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'phone_number', 'company', 'role')
    list_filter = ('is_deleted', 'role')
    search_fields = ('user__username', 'company__name', 'user__email')

    def username(self, obj):
        return f"{obj.user.username}"

    def email(self, obj):
        return f"{obj.user.email}"

    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def phone_number(self, obj):
        return f"{obj.user.profile.phone_number if obj.user.profile.phone_number else '-'}" if obj.user.profile else '-'


class CompanyColumns(admin.ModelAdmin):
    list_display = ('name', 'owner', 'number', 'city', 'foundation_date')
    list_filter = ('is_deleted', 'foundation_date')
    search_fields = ('name', 'created_by__username', 'number', 'city')

    def owner(self, obj):
        return f"{obj.created_by}"

class ProfileColumns(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', )


# Register your models here.
admin.site.register(models.Employee, EmployeeColumn)
admin.site.register(models.Company, CompanyColumns)
admin.site.register(models.Shift, ShiftColumn)
admin.site.register(models.Role)
admin.site.register(models.Profile, ProfileColumns)
