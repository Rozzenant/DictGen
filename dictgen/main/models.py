from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Роли пользователя
USER_ROLES_CHOICES = [
    ('student', 'Ученик'),
    ('teacher', 'Преподаватель'),
    ('admin', 'Администратор'),
]

# Типы сложности текста
TEXT_COMPLEXITY_CHOICES = [
    ('scientific', 'Научный'),
    ('narrative', 'Повествовательный'),
    ('colloquial', 'Разговорный'),
    ('technical', 'Технический'),
    ('artistic', 'Художественный'),
]

# Уровни сложности задания
DIFFICULTY_LEVELS_CHOICES = [
    ('easy', 'Легкий'),
    ('medium', 'Средний'),
    ('hard', 'Сложный'),
]

# Стадии выполнения попытки
ATTEMPT_STAGE_CHOICES = [
    ('created', 'Создано'),
    ('in_progress', 'В процессе'),
    ('submitted', 'Отправлено на проверку'),
    ('review', 'На проверке'),
    ('completed', 'Завершено'),
]


# Пользователь
class User(models.Model):
    username = models.CharField(max_length=48)
    email = models.EmailField(max_length=48)
    login = models.CharField(max_length=48)
    password = models.CharField(max_length=48)
    first_name = models.CharField(max_length=48)
    last_name = models.CharField(max_length=48)
    role = models.CharField(max_length=16, choices=USER_ROLES_CHOICES, default='student')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Термин
class Term(models.Model):
    content = models.CharField(max_length=32)
    length = models.IntegerField()
    subject = models.CharField(max_length=32)

    def __str__(self):
        return self.content


# Задание
class Task(models.Model):
    title = models.CharField(max_length=128)
    content = models.TextField()
    text_complexity = models.CharField(max_length=32, choices=TEXT_COMPLEXITY_CHOICES, default='narrative')
    status = models.CharField(max_length=16)
    difficulty = models.CharField(max_length=6, choices=DIFFICULTY_LEVELS_CHOICES, default='medium')
    length = models.IntegerField()
    min_words = models.IntegerField()
    max_words = models.IntegerField()
    min_sentences = models.IntegerField()
    max_sentences = models.IntegerField()
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, related_name='teacher_tasks', on_delete=models.CASCADE)
    terms = models.ManyToManyField(Term, through='TaskTerm')

    def __str__(self):
        return self.title


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
    error_type = models.CharField(max_length=24)
    position_start = models.IntegerField()
    position_end = models.IntegerField()
    true_variant = models.CharField(max_length=128)

    def __str__(self):
        return f"Error: {self.error_type} in attempt {self.attempt.id}"


# Метрики оценки задания
class Metric(models.Model):
    levenshtein = models.IntegerField()
    wer = models.FloatField()
    cer = models.FloatField()
    per = models.FloatField()
    accuracy = models.FloatField()
    word_error_count = models.IntegerField()
    punctuation_error_count = models.IntegerField()
    missing_word_count = models.IntegerField()
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Metrics: Accuracy {self.accuracy*100:.2f}%"


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
