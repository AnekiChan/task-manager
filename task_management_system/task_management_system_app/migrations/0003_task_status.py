# Generated by Django 5.1.4 on 2024-12-22 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management_system_app', '0002_task_is_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('planned', 'Запланировано'), ('in_progress', 'В работе'), ('completed', 'Завершено')], default='planned', max_length=20),
        ),
    ]
