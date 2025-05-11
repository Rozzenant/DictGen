from django.test import TestCase
from main.models import User, Task, Attempt
from main.utils import analyze_errors, calculate_metrics

class MetricsTestCase(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create(
            username="test_user",
            email="test@example.com",
            login="test",
            password="test123",
            first_name="Test",
            last_name="User",
            role="student"
        )
        
        # Создаем тестовое задание
        self.task = Task.objects.create(
            title="Test Task",
            content="Мама мыла раму. Папа читал газету.",
            text_complexity="narrative",
            status="active",
            difficulty="medium",
            length=len("Мама мыла раму. Папа читал газету."),
            min_words=5,
            max_words=10,
            min_sentences=2,
            max_sentences=2,
            user=self.user,
            teacher=self.user
        )
        
        # Создаем тестовую попытку с ошибками
        self.attempt = Attempt.objects.create(
            task=self.task,
            content="Мама мыла раму. Папа читал газету.",
            stage="submitted"
        )

    def test_perfect_attempt(self):
        """Тест для идеальной попытки без ошибок"""
        errors = analyze_errors(self.attempt)
        metrics = calculate_metrics(self.attempt)
        
        # Проверяем, что нет ошибок
        self.assertEqual(len(errors), 0)
        
        # Проверяем метрики
        self.assertEqual(metrics.levenshtein, 0)
        self.assertEqual(metrics.wer, 0.0)
        self.assertEqual(metrics.cer, 0.0)
        self.assertEqual(metrics.per, 0.0)
        self.assertEqual(metrics.accuracy, 1.0)
        self.assertEqual(metrics.word_error_count, 0)
        self.assertEqual(metrics.punctuation_error_count, 0)
        self.assertEqual(metrics.missing_word_count, 0)

    def test_spelling_errors(self):
        """Тест для попытки с орфографическими ошибками"""
        self.attempt.content = "Мама мыла раму. Папа читал газету."
        self.attempt.save()
        
        errors = analyze_errors(self.attempt)
        metrics = calculate_metrics(self.attempt)
        
        # Проверяем, что нет ошибок
        self.assertEqual(len(errors), 0)
        
        # Проверяем метрики
        self.assertEqual(metrics.levenshtein, 0)
        self.assertEqual(metrics.wer, 0.0)
        self.assertEqual(metrics.cer, 0.0)
        self.assertEqual(metrics.per, 0.0)
        self.assertEqual(metrics.accuracy, 1.0)

    def test_grammar_errors(self):
        """Тест для попытки с грамматическими ошибками"""
        self.attempt.content = "Мама мыла раму. Папа читал газеты."
        self.attempt.save()
        
        errors = analyze_errors(self.attempt)
        metrics = calculate_metrics(self.attempt)
        
        # Проверяем наличие ошибок
        self.assertGreater(len(errors), 0)
        
        # Проверяем метрики
        self.assertGreater(metrics.levenshtein, 0)
        self.assertGreater(metrics.wer, 0.0)
        self.assertGreater(metrics.cer, 0.0)
        self.assertGreater(metrics.per, 0.0)
        self.assertLess(metrics.accuracy, 1.0)

    def test_missing_words(self):
        """Тест для попытки с пропущенными словами"""
        self.attempt.content = "Мама раму. Папа читал газету."
        self.attempt.save()
        
        errors = analyze_errors(self.attempt)
        metrics = calculate_metrics(self.attempt)
        
        # Проверяем наличие ошибок
        self.assertGreater(len(errors), 0)
        
        # Проверяем метрики
        self.assertGreater(metrics.levenshtein, 0)
        self.assertGreater(metrics.wer, 0.0)
        self.assertGreater(metrics.cer, 0.0)
        self.assertGreater(metrics.per, 0.0)
        self.assertLess(metrics.accuracy, 1.0)
        self.assertGreater(metrics.missing_word_count, 0)

    def test_punctuation_errors(self):
        """Тест для попытки с пунктуационными ошибками"""
        self.attempt.content = "Мама мыла раму, Папа читал газету"
        self.attempt.save()
        
        errors = analyze_errors(self.attempt)
        metrics = calculate_metrics(self.attempt)
        
        # Проверяем наличие ошибок
        self.assertGreater(len(errors), 0)
        
        # Проверяем метрики
        self.assertGreater(metrics.levenshtein, 0)
        self.assertGreater(metrics.wer, 0.0)
        self.assertGreater(metrics.cer, 0.0)
        self.assertGreater(metrics.per, 0.0)
        self.assertLess(metrics.accuracy, 1.0)
        self.assertGreater(metrics.punctuation_error_count, 0) 