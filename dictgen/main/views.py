from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User, Term, Task, Attempt
from .serializers import UserSerializer, TermSerializer, TaskSerializer, AttemptSerializer, UserStatisticsSerializer
from .utils import analyze_errors
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, permissions
from rest_framework.decorators import action

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
    def get(self, request):
        tasks = Task.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(paginated_tasks, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Получение, обновление и удаление конкретного задания (GET, PUT, PATCH, DELETE)
class TaskDetailView(APIView):
    def get(self, request, id):
        task = get_object_or_404(Task, id=id)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        task = get_object_or_404(Task, id=id)
        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        task = get_object_or_404(Task, id=id)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        task = get_object_or_404(Task, id=id)
        task.delete()
        return Response({'message': f'Задание с ID {id} успешно удалено'}, status=status.HTTP_204_NO_CONTENT)

# Получение списка попыток и создание новой (GET, POST)
class AttemptListView(APIView):
    def get(self, request):
        attempts = Attempt.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_attempts = paginator.paginate_queryset(attempts, request)
        serializer = AttemptSerializer(paginated_attempts, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = AttemptSerializer(data=request.data)
        if serializer.is_valid():
            attempt = serializer.save()
            analyze_errors(attempt)  # Анализируем ошибки после сохранения
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Получение, обновление и удаление конкретной попытки (GET, PUT, DELETE)
class AttemptDetailView(APIView):
    def get(self, request, id):
        attempt = get_object_or_404(Attempt, id=id)
        serializer = AttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        attempt = get_object_or_404(Attempt, id=id)
        serializer = AttemptSerializer(attempt, data=request.data)
        if serializer.is_valid():
            attempt = serializer.save()
            analyze_errors(attempt)  # Перепроверяем ошибки при обновлении
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        user = self.get_object()
        serializer = UserStatisticsSerializer(user)
        return Response(serializer.data)
