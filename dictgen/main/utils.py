from .models import Error, Metric
import difflib
import re
import pymorphy3
from Levenshtein import distance as Levenshtein

# Создаем морфологический анализатор
morph = pymorphy3.MorphAnalyzer()

def analyze_errors(attempt):
    """
    Анализирует ошибки в попытке пользователя с использованием морфологического анализатора.
    Каждая попытка сохраняется со своими ошибками для отслеживания прогресса.
    """
    task = attempt.task
    task_text = task.content
    attempt_text = attempt.content

    # Создаем список для хранения ошибок
    errors = []

    # Сохраняем оригинальные тексты для определения позиций
    original_task_text = task_text
    original_attempt_text = attempt_text

    # Приводим тексты к нижнему регистру для сравнения
    task_text = task_text.lower()
    attempt_text = attempt_text.lower()
    
    # Разбиваем тексты на слова и знаки препинания
    task_tokens = re.findall(r"\w+|[.,:;!?—()""''…]", task_text)
    attempt_tokens = re.findall(r"\w+|[.,:;!?—()""''…]", attempt_text)
    
    # Создаем объект для сравнения последовательностей
    matcher = difflib.SequenceMatcher(None, task_tokens, attempt_tokens)
    
    # Анализируем различия
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # Найдены замененные слова
            task_word = " ".join(task_tokens[i1:i2])
            attempt_word = " ".join(attempt_tokens[j1:j2])
            
            # Определяем тип ошибки
            if any(c in '.,:;!?—()""''…' for c in task_word) or any(c in '.,:;!?—()""''…' for c in attempt_word):
                error_type = 'punctuation'  # Пунктуационная ошибка
            else:
                # Анализируем слова с помощью pymorphy3
                task_parse = morph.parse(task_word)
                attempt_parse = morph.parse(attempt_word)
                
                if task_parse and attempt_parse:
                    # Если оба слова найдены в словаре
                    task_normal = task_parse[0].normal_form
                    attempt_normal = attempt_parse[0].normal_form
                    
                    if task_normal == attempt_normal:
                        # Если нормальные формы совпадают - это грамматическая ошибка
                        error_type = 'grammar'
                    else:
                        # Если нормальные формы разные - это орфографическая ошибка
                        error_type = 'spelling'
                else:
                    # Если хотя бы одно слово не найдено в словаре
                    if len(task_word) == len(attempt_word):
                        error_type = 'spelling'
                    else:
                        error_type = 'grammar'
                
            position = original_attempt_text.lower().find(attempt_word)
            errors.append(Error(
                attempt=attempt,
                error_type=error_type,
                position_start=position,
                position_end=position + len(attempt_word),
                true_variant=task_word
            ))
            
        elif tag == 'delete':
            # Найдены пропущенные слова
            missing_word = " ".join(task_tokens[i1:i2])
            prev_pos = original_attempt_text.lower().find(attempt_tokens[j1-1]) + len(attempt_tokens[j1-1]) if j1 > 0 else 0
            
            # Определяем тип ошибки для пропущенных слов
            error_type = 'punctuation' if any(c in '.,:;!?—()""''…' for c in missing_word) else 'missing'
            
            errors.append(Error(
                attempt=attempt,
                error_type=error_type,
                position_start=prev_pos,
                position_end=prev_pos,
                true_variant=missing_word
            ))
            
        elif tag == 'insert':
            # Найдены лишние слова
            extra_word = " ".join(attempt_tokens[j1:j2])
            position = original_attempt_text.lower().find(extra_word)
            
            # Определяем тип ошибки для лишних слов
            error_type = 'punctuation' if any(c in '.,:;!?—()""''…' for c in extra_word) else 'extra'
            
            errors.append(Error(
                attempt=attempt,
                error_type=error_type,
                position_start=position,
                position_end=position + len(extra_word),
                true_variant=''
            ))
    
    # Сохраняем все ошибки одним запросом
    if errors:
        Error.objects.bulk_create(errors)
    
    return errors

def calculate_metrics(attempt):
    """
    Рассчитывает все метрики для попытки выполнения задания.
    """
    task = attempt.task
    task_text = task.content
    attempt_text = attempt.content

    # Разбиваем тексты на слова и символы
    task_words = re.findall(r"\w+|[.,:;!?—()""''…]", task_text.lower())
    attempt_words = re.findall(r"\w+|[.,:;!?—()""''…]", attempt_text.lower())
    
    # Разбиваем на символы для CER
    task_chars = list(task_text.lower())
    attempt_chars = list(attempt_text.lower())
    
    # Рассчитываем расстояние Левенштейна
    levenshtein_distance = Levenshtein.distance(task_text.lower(), attempt_text.lower())
    
    # Рассчитываем WER (Word Error Rate)
    word_errors = Levenshtein.distance(task_words, attempt_words)
    wer = word_errors / len(task_words) if task_words else 0
    
    # Рассчитываем CER (Character Error Rate)
    char_errors = Levenshtein.distance(task_chars, attempt_chars)
    cer = char_errors / len(task_chars) if task_chars else 0
    
    # Рассчитываем PER (Position Error Rate)
    matcher = difflib.SequenceMatcher(None, task_words, attempt_words)
    position_errors = sum(1 for tag, _, _, _, _ in matcher.get_opcodes() if tag != 'equal')
    per = position_errors / len(task_words) if task_words else 0
    
    # Рассчитываем точность
    accuracy = 1 - wer
    
    # Подсчитываем количество ошибок по типам
    errors = Error.objects.filter(attempt=attempt)
    word_error_count = errors.filter(error_type='spelling').count()
    punctuation_error_count = errors.filter(error_type='punctuation').count()
    missing_word_count = errors.filter(error_type='missing').count()
    
    # Создаем и сохраняем метрики
    metrics = Metric.objects.create(
        levenshtein=levenshtein_distance,
        wer=wer,
        cer=cer,
        per=per,
        accuracy=accuracy,
        word_error_count=word_error_count,
        punctuation_error_count=punctuation_error_count,
        missing_word_count=missing_word_count
    )
    
    return metrics
