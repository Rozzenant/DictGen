import os
import django
from django.test import TestCase

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dictgen.settings')
django.setup()

from main.models import User, Task, Attempt
from main.utils import analyze_errors

class ErrorDetectionTests(TestCase):
    def setUp(self):
        """Создание тестового пользователя и базовых данных"""
        self.user = User.objects.create(
            username='test_user',
            email='test@example.com',
            login='test',
            password='test123',
            first_name='Test',
            last_name='User',
            role='student'
        )

    def create_task_and_attempt(self, title, task_text, attempt_text):
        """Вспомогательный метод для создания задания и попытки"""
        task = Task.objects.create(
            title=title,
            content=task_text,
            text_complexity='narrative',
            status='active',
            difficulty='medium',
            length=len(task_text),
            min_words=5,
            max_words=100,
            min_sentences=1,
            max_sentences=10,
            user=self.user,
            teacher=self.user
        )
        
        attempt = Attempt.objects.create(
            task=task,
            content=attempt_text,
            stage='submitted'
        )
        
        return task, attempt

    def test_spelling_errors(self):
        """Тест на обнаружение орфографических ошибок"""
        task_text = "В библиотеке можно найти множество интересных книг."
        attempt_text = "В библеотеке можно найти множество интересных книг."
        
        task, attempt = self.create_task_and_attempt(
            "Тест орфографических ошибок",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].error_type, 'spelling')
        self.assertEqual(errors[0].true_variant, 'библиотеке')

    def test_grammar_errors(self):
        """Тест на обнаружение грамматических ошибок"""
        task_text = "Дети играют во дворе. Они веселятся."
        attempt_text = "Дети играет во дворе. Они веселится."
        
        task, attempt = self.create_task_and_attempt(
            "Тест грамматических ошибок",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(error.error_type == 'grammar' for error in errors))

    def test_missing_words(self):
        """Тест на обнаружение пропущенных слов"""
        task_text = "Утром я проснулся рано. Сделал зарядку и принял душ."
        attempt_text = "Утром проснулся рано. Сделал зарядку принял душ."
        
        task, attempt = self.create_task_and_attempt(
            "Тест пропущенных слов",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertEqual(len(errors), 2)  # Пропущены два союза "и"
        self.assertTrue(all(error.error_type == 'missing' for error in errors))

    def test_extra_words(self):
        """Тест на обнаружение лишних слов"""
        task_text = "Солнце светило ярко. Дети играли во дворе."
        attempt_text = "Солнце светило очень ярко. Дети играли весело во дворе."
        
        task, attempt = self.create_task_and_attempt(
            "Тест лишних слов",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertEqual(len(errors), 2)  # Лишние слова "очень" и "весело"
        self.assertTrue(all(error.error_type == 'extra' for error in errors))

    def test_punctuation_errors(self):
        """Тест на обнаружение пунктуационных ошибок"""
        task_text = "Привет! Как дела? Я только что вернулся из магазина."
        attempt_text = "Привет как дела я только что вернулся из магазина"
        
        task, attempt = self.create_task_and_attempt(
            "Тест пунктуационных ошибок",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any(error.error_type == 'punctuation' for error in errors))
        

    def test_multiple_errors(self):
        """Тест на обнаружение множественных ошибок разных типов"""
        task_text = "Вчера я ходил в магазин. Купил хлеб, молоко и яблоки."
        attempt_text = "Вчера я ходил в магозин. Купил хлеб и яблоки."
        
        task, attempt = self.create_task_and_attempt(
            "Тест множественных ошибок",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertTrue(len(errors) >= 2)
        error_types = {error.error_type for error in errors}
        self.assertTrue('spelling' in error_types or 'missing' in error_types)

    def test_complex_text(self):
        """Тест на анализ сложного текста с разными типами ошибок"""
        task_text = """Квантовая механика описывает поведение материи на атомном уровне.
        Основные принципы включают принцип неопределенности Гейзенберга.
        Эти концепции противоречат классической физике."""
        
        attempt_text = """Квантовая механика описывает поведение материи на атомном уровне
        Основные принципы включают принцип неопределености Гейзенберга
        Эти концепции противоречат классической физике"""
        
        task, attempt = self.create_task_and_attempt(
            "Тест сложного текста",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertTrue(len(errors) > 0)
        error_types = {error.error_type for error in errors}
        self.assertTrue('spelling' in error_types or 'punctuation' in error_types)

    def test_error_positions(self):
        """Тест на корректность определения позиций ошибок"""
        task_text = "В библиотеке много книг."
        attempt_text = "В библеотеке много книг."
        
        task, attempt = self.create_task_and_attempt(
            "Тест позиций ошибок",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertTrue(error.position_start < error.position_end)
        self.assertEqual(
            attempt_text[error.position_start:error.position_end],
            'библеотеке'
        )

    def test_no_errors(self):
        """Тест на случай отсутствия ошибок"""
        task_text = "Текст без ошибок."
        attempt_text = "Текст без ошибок."
        
        task, attempt = self.create_task_and_attempt(
            "Тест без ошибок",
            task_text,
            attempt_text
        )
        
        errors = analyze_errors(attempt)
        
        self.assertEqual(len(errors), 0)
