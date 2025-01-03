import json
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Category, Task, Notification, Comment
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.decorators import login_required


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

def is_admin(user):
    return user.is_superuser

admin_required = user_passes_test(lambda user: user.is_superuser)

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('category_list')
            else:
                return redirect('user_tasks_list')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


@login_required
def user_tasks_list(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    notifications = Notification.objects.filter(user=request.user, is_read=False)

    return render(request, 'user_tasks_list.html', {
        'tasks': tasks,
        'notifications_count': notifications.count()
    })

@login_required
def kanban_board(request):
    tasks_planned = Task.objects.filter(status='planned')
    tasks_in_progress = Task.objects.filter(status='in_progress')
    tasks_completed = Task.objects.filter(status='completed')
    return render(request, 'kanban_board.html', {
        'tasks_planned': tasks_planned,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
    })

@login_required
def all_tasks_list(request):
    tasks = Task.objects.select_related('category', 'assigned_to').all()
    return render(request, 'all_tasks_list.html', {'tasks': tasks})

@csrf_exempt
def update_task_status(request, task_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        status = data.get('status')
        task = Task.objects.get(id=task_id)
        task.status = status
        task.save()
        return JsonResponse({'status': 'success'})

@login_required
def add_comment(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                task=task,
                author=request.user,
                content=content
            )
            # Создаем уведомление для владельца задачи
            if task.assigned_to != request.user:
                Notification.objects.create(
                    user=task.assigned_to,
                    task=task,
                    content=f"Новый комментарий к вашей задаче: {task.name}"
                )
        return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        return HttpResponseForbidden()

@login_required
def notifications_list(request):
    notifications = Notification.objects.select_related('task').filter(user=request.user).order_by('-created_at')
    notifications.update(is_read=True)
    return render(request, 'notifications_list.html', {'notifications': notifications})

@login_required
def mark_notifications_as_read(request):
    if request.method == "POST":
        try:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login(request, user)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def LogoutPage(request):
    logout(request)
    return redirect("login")


@login_required
@admin_required
def delete_task(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(id=task_id)
        task.delete()
    return redirect(reverse('category_list'))


@login_required
@admin_required
def create_task(request):
    if request.method == 'POST':
        # Retrieve data from the POST request
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        priority = request.POST.get('priority')
        description = request.POST.get('description')
        #location = request.POST.get('location')
        #organizer = request.POST.get('organizer')
        assigned_to_id = request.POST.get('assigned_to')

        category = Category.objects.get(pk=category_id)
        assigned_to = User.objects.get(pk=assigned_to_id)

        task = Task.objects.create(
            name=name,
            category=category,
            start_date=start_date,
            end_date=end_date,
            priority=priority,
            description=description,
            assigned_to=assigned_to
        )

        Notification.objects.create(
            user=task.assigned_to,
            task=task,
            content=f"Новая задача"
        )

        return redirect('category_list')
    else:
        categories = Category.objects.all()
        users = User.objects.all()
        return render(request, 'create_task.html', {'categories': categories, 'users': users})



@login_required
@admin_required
def update_task(request, task_id):
    task = Task.objects.get(pk=task_id)
    if request.method == 'POST':
        # Update task fields based on form data
        task.name = request.POST.get('name')
        task.start_date = request.POST.get('start_date')
        task.end_date = request.POST.get('end_date')
        task.priority = request.POST.get('priority')
        task.description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            task.assigned_to_id = int(assigned_to_id)
        else:
            task.assigned_to_id = None
        task.save()
        Notification.objects.create(
            user=task.assigned_to,
            task=task,
            content=f"Задача обновлена"
        )
        return redirect('category_list')
    else:
        users = User.objects.all()
        return render(request, 'update_task.html', {'task': task, 'users': users})

@csrf_exempt
@login_required
def update_task_status(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.get(pk=task_id)
            data = json.loads(request.body)
            new_status = data.get('status')

            if new_status not in dict(Task.STATUS_CHOICES):
                return JsonResponse({'error': 'Invalid status'}, status=400)

            task.status = new_status
            task.save()
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
@admin_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})


@login_required
@admin_required
def create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Category.objects.create(name=name)
        return redirect('category_list')
    return render(request, 'create_category.html')


@login_required
@admin_required
def delete_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    if category.task_set.exists():
        messages.error(
            request, "Вы не можете удалить раздел, пока в нём есть задачи.")
    else:
        category.delete()
        messages.success(request, "Раздел удалён.")
    return redirect('category_list')


@login_required
@admin_required
def category_tasks(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    tasks = category.task_set.all()
    return render(request, 'category_tasks.html', {'category': category, 'tasks': tasks})


@login_required
@admin_required
def task_chart(request):
    categories = Category.objects.all()
    pending_counts = {}
    for category in categories:
        pending_counts[category.name] = Task.objects.filter(
            category=category,
            start_date__gt=timezone.now()
        ).count()
    return render(request, 'task_chart.html', {'pending_counts': pending_counts})
