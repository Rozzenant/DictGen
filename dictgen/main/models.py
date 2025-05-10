from django.db import models

class User(models.Model):
    USERNAME = models.CharField(max_length=48)
    EMAIL = models.CharField(max_length=48)
    LOGIN = models.CharField(max_length=48)
    PASSWORD = models.CharField(max_length=48)
    FIRST_NAME = models.CharField(max_length=48)
    SECOND_NAME = models.CharField(max_length=48)
    ROLE = models.CharField(max_length=16)

class Term(models.Model):
    TERM_CONTENT = models.CharField(max_length=32)
    TERM_LENGTH = models.IntegerField()
    SUBJECT = models.CharField(max_length=32)

class Task(models.Model):
    TITLE = models.CharField(max_length=128)
    CONTENT = models.TextField()
    TEXT_COMPLEXITY = models.CharField(max_length=32)
    STATUS = models.CharField(max_length=16)
    DIFFICULTY = models.CharField(max_length=6)
    LENGTH = models.IntegerField()
    MIN_WORDS = models.IntegerField()
    MAX_WORDS = models.IntegerField()
    NUMBER_OF_MIN_SENTENCE = models.IntegerField()
    NUMBER_OF_MAX_SENTENCE = models.IntegerField()
    CREATION_DATE = models.DateTimeField()
    LAST_MODIFIED = models.DateTimeField()
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    TEACHER_ID = models.ForeignKey(User, related_name='teacher_tasks', on_delete=models.CASCADE)
    TASK_TERMS = models.ManyToManyField(Term, through='TaskTerm')

class TaskTerm(models.Model):
    TASK_ID = models.ForeignKey(Task, on_delete=models.CASCADE)
    TERM_ID = models.ForeignKey(Term, on_delete=models.CASCADE)

class Attempt(models.Model):
    TASK_ID = models.ForeignKey(Task, on_delete=models.CASCADE)
    ATTEMPT_CONTENT = models.TextField()

class Error(models.Model):
    ATTEMPT_ID = models.ForeignKey(Attempt, on_delete=models.CASCADE)
    ERROR_TYPE = models.CharField(max_length=24)
    POSITION_START = models.IntegerField()
    POSITION_END = models.IntegerField()
    TRUE_VARIANT = models.CharField(max_length=128)

class Metric(models.Model):
    LEVENSHTEIN = models.IntegerField()
    WER = models.FloatField()
    CER = models.FloatField()
    PER = models.FloatField()
    ACCURACY = models.FloatField()
    WORD_ERROR_COUNT = models.IntegerField()
    PUNCTUATION_ERROR_COUNT = models.IntegerField()
    MISSING_WORD_COUNT = models.IntegerField()
    CREATION_DATE = models.DateTimeField()

class Statistics(models.Model):
    TOTAL_ATTEMPTS = models.IntegerField()
    CORRECT_ATTEMPTS = models.IntegerField()
    INCORRECT_ATTEMPTS = models.IntegerField()
    TOTAL_ERRORS = models.IntegerField()
    WER = models.FloatField()
    CER = models.FloatField()
    PER = models.FloatField()
    AVR_ERRORS_PER_ATTEMPT = models.FloatField()
    ACCURACY = models.FloatField()
    LAST_ERROR_DATE = models.DateTimeField()
    WORD_ERRORS = models.IntegerField()
    PUNCTUATION_ERRORS = models.IntegerField()
    MISSING_WORD_ERRORS = models.IntegerField()
