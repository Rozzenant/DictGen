from rest_framework import serializers
from .models import User, Term, Task, Attempt, Metric, Error

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

class UserStatisticsSerializer(serializers.ModelSerializer):
    total_attempts = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()
    average_accuracy = serializers.SerializerMethodField()
    average_wer = serializers.SerializerMethodField()
    average_cer = serializers.SerializerMethodField()
    average_per = serializers.SerializerMethodField()
    error_statistics = serializers.SerializerMethodField()
    recent_attempts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'total_attempts', 'total_tasks', 'average_accuracy',
            'average_wer', 'average_cer', 'average_per',
            'error_statistics', 'recent_attempts'
        ]

    def get_total_attempts(self, obj):
        return Attempt.objects.filter(task__user=obj).count()

    def get_total_tasks(self, obj):
        return Task.objects.filter(user=obj).count()

    def get_average_accuracy(self, obj):
        metrics = Metric.objects.filter(attempt__task__user=obj)
        if not metrics:
            return 0
        return sum(m.accuracy for m in metrics) / len(metrics)

    def get_average_wer(self, obj):
        metrics = Metric.objects.filter(attempt__task__user=obj)
        if not metrics:
            return 0
        return sum(m.wer for m in metrics) / len(metrics)

    def get_average_cer(self, obj):
        metrics = Metric.objects.filter(attempt__task__user=obj)
        if not metrics:
            return 0
        return sum(m.cer for m in metrics) / len(metrics)

    def get_average_per(self, obj):
        metrics = Metric.objects.filter(attempt__task__user=obj)
        if not metrics:
            return 0
        return sum(m.per for m in metrics) / len(metrics)

    def get_error_statistics(self, obj):
        errors = Error.objects.filter(attempt__task__user=obj)
        total_errors = errors.count()
        if total_errors == 0:
            return {
                'spelling': 0,
                'grammar': 0,
                'punctuation': 0,
                'missing': 0,
                'extra': 0
            }
        
        return {
            'spelling': errors.filter(error_type='spelling').count() / total_errors,
            'grammar': errors.filter(error_type='grammar').count() / total_errors,
            'punctuation': errors.filter(error_type='punctuation').count() / total_errors,
            'missing': errors.filter(error_type='missing').count() / total_errors,
            'extra': errors.filter(error_type='extra').count() / total_errors
        }

    def get_recent_attempts(self, obj):
        recent_attempts = Attempt.objects.filter(task__user=obj).order_by('-id')[:5]
        return [{
            'task_title': attempt.task.title,
            'accuracy': attempt.metrics.accuracy if hasattr(attempt, 'metrics') else 0,
            'wer': attempt.metrics.wer if hasattr(attempt, 'metrics') else 0,
            'date': attempt.task.creation_date
        } for attempt in recent_attempts]