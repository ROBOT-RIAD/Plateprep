from django.contrib import admin
from .models import Task
# Register your models here.


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'assigned_by', 'assigned_to', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('task_name', 'assigned_by__email', 'assigned_to__email')
