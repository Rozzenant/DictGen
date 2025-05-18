from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from .constants import *

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=48, unique=True)
    email = models.EmailField(max_length=48, unique=True)
    first_name = models.CharField(max_length=48)
    last_name = models.CharField(max_length=48)
    role = models.CharField(max_length=16, choices=USER_ROLES_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    password = models.CharField(max_length=128)  # Для хранения хешированных паролей

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.username

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Термин
class Term(models.Model):
    content = models.CharField(max_length=128)
    length = models.IntegerField(editable=False)  # Длина вычисляется автоматически
    subject = models.CharField(max_length=32)

    def save(self, *args, **kwargs):
        # Вычисляем длину термина автоматически
        self.length = len(self.content)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content} ({self.subject})"


# Модель задания
class Task(models.Model):
    title = models.CharField(max_length=128)
    content = models.TextField()
    text_complexity = models.CharField(max_length=32, choices=TEXT_COMPLEXITY_CHOICES, default='narrative')
    status = models.CharField(max_length=16, choices=TASK_STATUS_CHOICES, default='draft')
    difficulty = models.CharField(max_length=6, choices=DIFFICULTY_LEVELS_CHOICES, default='medium')
    length = models.IntegerField()
    min_words = models.IntegerField()
    max_words = models.IntegerField()
    min_sentences = models.IntegerField()
    max_sentences = models.IntegerField()
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    teacher = models.ForeignKey('User', related_name='teacher_tasks', on_delete=models.CASCADE)
    terms = models.ManyToManyField('Term', through='TaskTerm')
    is_public = models.BooleanField(default=True)  # Общее задание или нет
    assigned_user = models.ForeignKey('User', null=True, blank=True, related_name='assigned_tasks', on_delete=models.SET_NULL)

    def clean(self):
        # Проверка: пользователь может назначить задание себе или преподаватель/админ может назначить другому
        if self.assigned_user and self.assigned_user != self.user:  # если назначается другому пользователю
            if self.teacher.role not in ['teacher', 'admin']:
                raise ValidationError("Только преподаватель или администратор могут назначать задания другим пользователям.")

        # Проверка: кто может создавать задания
        if self.teacher.role not in ['student', 'teacher', 'admin']:
            raise ValidationError("Только пользователь, преподаватель или администратор могут создавать задания.")

    def save(self, *args, **kwargs):
        # Перед сохранением проверяем корректность данных
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        assigned = f" -> {self.assigned_user.username}" if self.assigned_user else ""
        return f"{self.title} ({self.get_status_display()}){assigned}"


# Связь Задание-Термин
class TaskTerm(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    def __str__(self):
        return f"Task: {self.task.title}"


# Попытка выполнения задания
class Attempt(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    content = models.TextField()
    grade = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Оценка по 100-балльной шкале (0-100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    stage = models.CharField(max_length=16, choices=ATTEMPT_STAGE_CHOICES, default='created')

    def __str__(self):
        return f"Attempt for task: {self.task.title}, Stage: {self.get_stage_display()}, Grade: {self.grade if self.grade is not None else 'Не оценено'}"


# Ошибка в попытке
class Error(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE)
    error_type = models.CharField(max_length=24, choices=ERROR_TYPES_CHOICES)
    position_start = models.IntegerField()
    position_end = models.IntegerField()
    true_variant = models.TextField()

    def __str__(self):
        return f"Error: {self.error_type} in attempt {self.attempt.id}"


# Метрики оценки задания
class Metric(models.Model):
    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name='metrics')
    levenshtein = models.IntegerField()
    wer = models.FloatField()  # Word Error Rate
    cer = models.FloatField()  # Character Error Rate
    per = models.FloatField()  # Position Error Rate
    accuracy = models.FloatField()
    word_error_count = models.IntegerField(default=0)
    punctuation_error_count = models.IntegerField(default=0)
    missing_word_count = models.IntegerField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Metrics: Accuracy {self.accuracy*100:.2f}% для попытки {self.attempt.id}"


# Статистика попыток
class Statistics(models.Model):
    total_attempts = models.IntegerField()
    correct_attempts = models.IntegerField()
    incorrect_attempts = models.IntegerField()
    total_errors = models.IntegerField()
    wer = models.FloatField()
    cer = models.FloatField()
    per = models.FloatField()
    avg_errors_per_attempt = models.FloatField()
    accuracy = models.FloatField()
    last_error_date = models.DateTimeField()
    word_errors = models.IntegerField()
    punctuation_errors = models.IntegerField()
    missing_word_errors = models.IntegerField()

    def __str__(self):
        return f"Statistics: Accuracy {self.accuracy*100:.2f}%"
