"""
URL configuration for dictgen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from main import views

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    
    
    # Пользователи
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:id>/', views.UserDetailUpdateDeleteView.as_view(), name='user-detail-update-delete'),

    # Термины
    path('terms/', views.TermListView.as_view(), name='term-list'),
    path('terms/<int:id>/', views.TermDetailView.as_view(), name='term-detail'),

    # Задания
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/<int:id>/', views.TaskDetailView.as_view(), name='task-detail'),


    # Попытки выполнения
    path('attempts/', views.AttemptListView.as_view(), name='attempt-list'),
    path('attempts/<int:id>/', views.AttemptDetailView.as_view(), name='attempt-detail'),

    # # Метрики
    # path('metrics/', views.MetricListView.as_view(), name='metric-list'),
    # path('metrics/<int:id>/', views.MetricDetailView.as_view(), name='metric-detail'),

    # # Статистика
    # path('statistics/', views.StatisticsListView.as_view(), name='statistics-list'),
    # path('statistics/<int:id>/', views.StatisticsDetailView.as_view(), name='statistics-detail'),
]
