from rest_framework import serializers
from .models import User, Term, Task, Attempt

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'login', 'password', 'first_name', 'last_name', 'role']

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ['id', 'content', 'length', 'subject']
        
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'content', 'text_complexity', 'status', 'difficulty',
            'length', 'min_words', 'max_words', 'min_sentences', 'max_sentences',
            'creation_date', 'last_modified', 'user', 'teacher', 'is_public', 
            'assigned_user', 'terms'
        ]

class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = [
            'id', 'task', 'content', 'grade', 'stage'
        ]