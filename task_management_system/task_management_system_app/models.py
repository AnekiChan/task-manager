from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)


class Task(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершено'),
    ]

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    priority = models.IntegerField(default=1)
    description = models.TextField(default='')
    #location = models.CharField(max_length=255, default='')
    #organizer = models.CharField(max_length=100, default='')
    is_completed = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.task.name}"
