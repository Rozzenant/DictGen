from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Term, Task, Attempt, Metric, Error
from .utils import analyze_errors
from Levenshtein import distance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'is_active')

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ['id', 'content', 'length', 'subject']
        
class TaskSerializer(serializers.ModelSerializer):
    terms = TermSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'content', 'text_complexity', 'status', 'difficulty',
            'length', 'min_words', 'max_words', 'min_sentences', 'max_sentences',
            'creation_date', 'last_modified', 'user', 'teacher', 'is_public', 
            'assigned_user', 'terms'
        ]
        
    def create(self, validated_data):
        terms_data = self.initial_data.get('terms', [])
        task = Task.objects.create(**validated_data)
        if terms_data:
            task.terms.set(terms_data)
        return task

    def update(self, instance, validated_data):
        terms_data = self.initial_data.get('terms', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if terms_data is not None:
            instance.terms.set(terms_data)
        return instance

class AttemptSerializer(serializers.ModelSerializer):
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = [
            'id', 'task', 'content', 'grade', 'stage', 'metrics'
        ]

    def get_metrics(self, obj):
        try:
            return {
                'accuracy': obj.metrics.accuracy,
                'wer': obj.metrics.wer,
                'cer': obj.metrics.cer,
                'per': obj.metrics.per,
                'word_error_count': obj.metrics.word_error_count,
                'punctuation_error_count': obj.metrics.punctuation_error_count,
                'missing_word_count': obj.metrics.missing_word_count
            }
        except Metric.DoesNotExist:
            return None

    def create(self, validated_data):
        # Создаем попытку
        attempt = Attempt.objects.create(**validated_data)
        
        # Анализируем ошибки
        errors = analyze_errors(attempt)
        
        # Вычисляем метрики
        task_text = attempt.task.content
        attempt_text = attempt.content
        
        # Расстояние Левенштейна
        levenshtein = distance(task_text, attempt_text)
        
        # Word Error Rate (WER)
        task_words = task_text.split()
        attempt_words = attempt_text.split()
        word_errors = sum(1 for i in range(min(len(task_words), len(attempt_words))) if task_words[i] != attempt_words[i])
        wer = word_errors / len(task_words) if task_words else 0
        
        # Character Error Rate (CER)
        cer = levenshtein / len(task_text) if task_text else 0
        
        # Position Error Rate (PER)
        total_positions = len(task_text)
        error_positions = sum(1 for i in range(min(len(task_text), len(attempt_text))) if task_text[i] != attempt_text[i])
        per = error_positions / total_positions if total_positions else 0
        
        # Accuracy
        accuracy = 1 - (levenshtein / max(len(task_text), len(attempt_text)))
        
        # Подсчет ошибок по типам
        word_error_count = len([e for e in errors if e.error_type in ['spelling', 'grammar']])
        punctuation_error_count = len([e for e in errors if e.error_type == 'punctuation'])
        missing_word_count = len([e for e in errors if e.error_type == 'missing'])
        
        # Создаем метрику
        Metric.objects.create(
            attempt=attempt,
            levenshtein=levenshtein,
            wer=wer,
            cer=cer,
            per=per,
            accuracy=accuracy,
            word_error_count=word_error_count,
            punctuation_error_count=punctuation_error_count,
            missing_word_count=missing_word_count
        )
        
        return attempt

    def update(self, instance, validated_data):
        # Обновляем попытку
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем метрики
        task_text = instance.task.content
        attempt_text = instance.content
        
        # Расстояние Левенштейна
        levenshtein = distance(task_text, attempt_text)
        
        # Word Error Rate (WER)
        task_words = task_text.split()
        attempt_words = attempt_text.split()
        word_errors = sum(1 for i in range(min(len(task_words), len(attempt_words))) if task_words[i] != attempt_words[i])
        wer = word_errors / len(task_words) if task_words else 0
        
        # Character Error Rate (CER)
        cer = levenshtein / len(task_text) if task_text else 0
        
        # Position Error Rate (PER)
        total_positions = len(task_text)
        error_positions = sum(1 for i in range(min(len(task_text), len(attempt_text))) if task_text[i] != attempt_text[i])
        per = error_positions / total_positions if total_positions else 0
        
        # Accuracy
        accuracy = 1 - (levenshtein / max(len(task_text), len(attempt_text)))
        
        # Анализируем ошибки
        errors = analyze_errors(instance)
        
        # Подсчет ошибок по типам
        word_error_count = len([e for e in errors if e.error_type in ['spelling', 'grammar']])
        punctuation_error_count = len([e for e in errors if e.error_type == 'punctuation'])
        missing_word_count = len([e for e in errors if e.error_type == 'missing'])
        
        # Обновляем или создаем метрику
        metric, created = Metric.objects.get_or_create(attempt=instance)
        metric.levenshtein = levenshtein
        metric.wer = wer
        metric.cer = cer
        metric.per = per
        metric.accuracy = accuracy
        metric.word_error_count = word_error_count
        metric.punctuation_error_count = punctuation_error_count
        metric.missing_word_count = missing_word_count
        metric.save()
        
        return instance

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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Пароли не совпадают"})
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs