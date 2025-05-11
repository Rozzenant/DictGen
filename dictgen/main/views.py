from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User, Term, Task, Attempt
from .serializers import UserSerializer, TermSerializer, TaskSerializer, AttemptSerializer
from .utils import analyze_errors

# Чтение всех пользователей и создание нового (READ ALL, CREATE)
class UserListCreateView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Чтение, обновление и удаление конкретного пользователя (READ ONE, UPDATE, DELETE)
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
        return Response({'message': f'Пользователь с ID {id} удалён'}, status=status.HTTP_204_NO_CONTENT)

# Получение всех терминов и создание нового (GET, POST)
class TermListView(APIView):
    def get(self, request):
        terms = Term.objects.all()
        serializer = TermSerializer(terms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

# Получение всех заданий и создание нового (GET, POST)
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

class AttemptListView(APIView):
    def get(self, request):
        attempts = Attempt.objects.all()
        serializer = AttemptSerializer(attempts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AttemptSerializer(data=request.data)
        if serializer.is_valid():
            attempt = serializer.save()
            analyze_errors(attempt)  # Анализируем ошибки после сохранения
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
