from django.db import models
from accounts.models import User
from .constants import STATUS_CHOICES
# Create your models here.


class Task(models.Model):
    task_name = models.CharField(max_length=255)
    date = models.DateField()
    duration = models.DurationField(help_text="Duration format: hh:mm:ss")
    email = models.EmailField(help_text="Notification email or related email")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    assigned_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name='tasks_assigned')
    assigned_to = models.ForeignKey(User,on_delete=models.CASCADE,related_name='tasks_received')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_name} assigned by {self.assigned_by.email} to {self.assigned_to.email}"