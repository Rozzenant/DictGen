from .models import Error, Attempt, Task
import difflib

# Список возможных ошибок для слабослышащих
error_types = [
    ('spelling', 'Орфографическая ошибка'),
    ('grammar', 'Грамматическая ошибка'),
    ('ending', 'Ошибка в окончании'),
    ('preposition', 'Ошибка в предлоге'),
    ('agreement', 'Ошибка в согласовании'),
    ('punctuation', 'Ошибка в пунктуации'),
    ('extra_word', 'Лишнее слово'),
    ('missing_word', 'Пропущенное слово'),
    ('phonetic', 'Фонетическая ошибка'),
]

def analyze_errors(attempt):
    task = attempt.task
    task_words = task.content.split()
    attempt_words = attempt.content.split()

    # Очистка старых ошибок
    Error.objects.filter(attempt=attempt).delete()

    # Сравнение слов в задании и попытке
    matcher = difflib.SequenceMatcher(None, task_words, attempt_words)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            error_type = 'spelling'  # Пример: заменить "алгоритм" на "олгоритм"
            Error.objects.create(
                attempt=attempt,
                error_type=error_type,
                position_start=j1,
                position_end=j2,
                true_variant=" ".join(task_words[i1:i2])
            )
        elif tag == 'delete':
            error_type = 'missing_word'  # Пропущено слово
            Error.objects.create(
                attempt=attempt,
                error_type=error_type,
                position_start=j1,
                position_end=j1,
                true_variant=" ".join(task_words[i1:i2])
            )
        elif tag == 'insert':
            error_type = 'extra_word'  # Лишнее слово
            Error.objects.create(
                attempt=attempt,
                error_type=error_type,
                position_start=j1,
                position_end=j2,
                true_variant=" ".join(attempt_words[j1:j2])
            )