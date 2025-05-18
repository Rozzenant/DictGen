from rest_framework import permissions

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['teacher', 'admin']

class IsOwnerOrTeacher(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Проверяем, является ли пользователь владельцем объекта
        if hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        elif hasattr(obj, 'assigned_user'):
            is_owner = obj.assigned_user == request.user
        else:
            is_owner = False

        # Преподаватель или админ имеет доступ
        is_teacher = request.user.role in ['teacher', 'admin']
        
        return is_owner or is_teacher

class StudentTaskPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Студент может видеть/редактировать только свои задания или публичные
        if request.user.role == 'student':
            # Для GET запросов разрешаем доступ к публичным заданиям
            if request.method == 'GET':
                return obj.is_public or obj.user == request.user
            # Для остальных методов (PUT, DELETE) только свои задания
            return obj.user == request.user
        # Преподаватель и админ видят все
        return request.user.role in ['teacher', 'admin']

class StudentAttemptPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Студент может видеть только свои попытки
        if request.user.role == 'student':
            return obj.task.assigned_user == request.user
        # Преподаватель и админ видят все
        return request.user.role in ['teacher', 'admin'] 