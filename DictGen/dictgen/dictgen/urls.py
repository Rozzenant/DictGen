from django.contrib import admin
from django.urls import path, include
from main import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# Создаем роутер для API
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

# API маршруты
api_patterns = [
    # Аутентификация
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
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
]

urlpatterns = [
    # Root URL
    path('', views.RootView.as_view(), name='root'),
    
    # Админка
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include([
        # Включаем все API маршруты
        path('', include(api_patterns)),
        # Включаем роутер для ViewSet'ов
        path('', include(router.urls)),
        # Генерация текста
        path('generate-text/', views.GenerateTextView.as_view(), name='generate-text'),
    ])),
]
