from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import models
from .models import User, Term, Task, Attempt
from .serializers import UserSerializer, TermSerializer, TaskSerializer, AttemptSerializer, UserStatisticsSerializer, RegisterSerializer, LoginSerializer, ChangePasswordSerializer
from .utils import analyze_errors
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .permissions import IsOwnerOrTeacher, StudentTaskPermission, StudentAttemptPermission
from .llm_generator import get_generator
import logging
import time
from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)

# Главная страница
class RootView(APIView):
    def get(self, request):
        return Response({
            'message': 'Добро пожаловать в DictGen API',
            'endpoints': {
                'users': '/users/',
                'terms': '/terms/',
                'tasks': '/tasks/',
                'attempts': '/attempts/',
            }
        })

# Получение списка пользователей и создание нового (GET, POST)
class UserListCreateView(APIView):
    def get(self, request):
        users = User.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Получение, обновление и удаление конкретного пользователя (GET, PUT, DELETE)
class UserDetailUpdateDeleteView(APIView):
    def get(self, request, id):
        user = get_object_or_404(User, id=id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        user = get_object_or_404(User, id=id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        user = get_object_or_404(User, id=id)
        user.delete()
        return Response({'message': f'Пользователь с ID {id} успешно удалён'}, status=status.HTTP_204_NO_CONTENT)

# Получение списка терминов и создание нового (GET, POST)
class TermListView(APIView):
    def get(self, request):
        terms = Term.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_terms = paginator.paginate_queryset(terms, request)
        serializer = TermSerializer(paginated_terms, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TermSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Получение, обновление и удаление конкретного термина (GET, PUT, DELETE)
class TermDetailView(APIView):
    def get(self, request, id):
        term = get_object_or_404(Term, id=id)
        serializer = TermSerializer(term)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        term = get_object_or_404(Term, id=id)
        serializer = TermSerializer(term, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        term = get_object_or_404(Term, id=id)
        term.delete()
        return Response({'message': f'Термин с ID {id} успешно удалён'}, status=status.HTTP_204_NO_CONTENT)

# Получение списка заданий и создание нового (GET, POST)
class TaskListView(APIView):
    permission_classes = [permissions.IsAuthenticated, StudentTaskPermission]

    def get(self, request):
        if request.user.role == 'student':
            # Студент видит свои задания и публичные задания
            tasks = Task.objects.filter(
                models.Q(user=request.user) | 
                models.Q(is_public=True)
            )
        else:
            tasks = Task.objects.all()
            
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(paginated_tasks, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            # Если пользователь студент, устанавливаем его как создателя задания
            if request.user.role == 'student':
                serializer.validated_data['user'] = request.user
                serializer.validated_data['teacher'] = request.user
                serializer.validated_data['is_public'] = False  # Студенческие задания не публичные по умолчанию
                serializer.validated_data['assigned_user'] = request.user  # Автоматически назначаем задание создателю
            
            task = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Получение, обновление и удаление конкретного задания (GET, PUT, PATCH, DELETE)
class TaskDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, StudentTaskPermission]

    def get(self, request, id):
        task = get_object_or_404(Task, id=id)
        self.check_object_permissions(request, task)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        task = get_object_or_404(Task, id=id)
        self.check_object_permissions(request, task)
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            # Если пользователь студент, проверяем что он не меняет критические поля
            if request.user.role == 'student':
                protected_fields = ['is_public', 'teacher', 'assigned_user']
                for field in protected_fields:
                    if field in serializer.validated_data:
                        return Response(
                            {'error': f'Студенты не могут изменять поле {field}'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            task = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        task = get_object_or_404(Task, id=id)
        self.check_object_permissions(request, task)
        
        # Студенты могут удалять только свои задания
        if request.user.role == 'student' and task.user != request.user:
            return Response(
                {'error': 'Вы можете удалять только свои задания'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        task.delete()
        return Response({'message': f'Задание с ID {id} успешно удалено'}, status=status.HTTP_204_NO_CONTENT)

# Получение списка попыток и создание новой (GET, POST)
class AttemptListView(APIView):
    permission_classes = [permissions.IsAuthenticated, StudentAttemptPermission]

    def get(self, request):
        if request.user.role == 'student':
            attempts = Attempt.objects.filter(task__assigned_user=request.user)
        else:
            attempts = Attempt.objects.all()
            
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_attempts = paginator.paginate_queryset(attempts, request)
        serializer = AttemptSerializer(paginated_attempts, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = AttemptSerializer(data=request.data)
        if serializer.is_valid():
            # Проверяем, что студент создает попытку только для своего задания
            task = Task.objects.get(id=serializer.validated_data['task'].id)
            if request.user.role == 'student' and task.assigned_user != request.user:
                return Response(
                    {'error': 'Вы можете создавать попытки только для своих заданий'},
                    status=status.HTTP_403_FORBIDDEN
                )
            attempt = serializer.save()
            analyze_errors(attempt)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Получение, обновление и удаление конкретной попытки (GET, PUT, DELETE)
class AttemptDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, StudentAttemptPermission]

    def get(self, request, id):
        attempt = get_object_or_404(Attempt, id=id)
        self.check_object_permissions(request, attempt)
        serializer = AttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        attempt = get_object_or_404(Attempt, id=id)
        self.check_object_permissions(request, attempt)
        serializer = AttemptSerializer(attempt, data=request.data)
        if serializer.is_valid():
            attempt = serializer.save()
            analyze_errors(attempt)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        if request.user.role == 'student':
            return Response(
                {'error': 'Студенты не могут удалять попытки'},
                status=status.HTTP_403_FORBIDDEN
            )
        attempt = get_object_or_404(Attempt, id=id)
        attempt.delete()
        return Response({'message': f'Попытка с ID {id} успешно удалена'}, status=status.HTTP_204_NO_CONTENT)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['teacher', 'admin']:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        user = self.get_object()
        if request.user.role == 'student' and request.user.id != int(pk):
            return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserStatisticsSerializer(user)
        return Response(serializer.data)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response(
                {'error': 'Неверные учетные данные'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Пароль успешно изменен'})
            return Response(
                {'error': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Успешный выход из системы'})
        except Exception:
            return Response(
                {'error': 'Неверный токен'},
                status=status.HTTP_400_BAD_REQUEST
            )

class GenerateTextView(APIView):
    def post(self, request):
        try:
            # Получаем термины из запроса
            term_ids = request.data.get('terms', [])
            
            # Проверяем наличие терминов
            if not term_ids:
                return Response(
                    {"error": "Не указаны термины для генерации"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Получаем объекты терминов
            terms = Term.objects.filter(id__in=term_ids)
            if not terms:
                return Response(
                    {"error": "Термины не найдены"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Генерируем текст
            start_time = time.time()
            logger.info(f"Начало генерации текста. Термины: {[term.content for term in terms]}")
            
            try:
                generator = get_generator()
                response_text = generator.generate(terms)
                
                execution_time = time.time() - start_time
                logger.info(f"Генерация текста завершена. Время выполнения: {execution_time:.2f} сек.")
                
                return Response({
                    "text": response_text,
                    "execution_time": execution_time
                })
                
            except Exception as e:
                logger.error(f"Ошибка при генерации текста: {str(e)}")
                return Response(
                    {"error": f"Ошибка генерации текста: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Ошибка в API: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
