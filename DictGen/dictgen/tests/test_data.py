from main.models import User, Task, Attempt
from main.utils import analyze_errors, calculate_metrics

def print_metrics(task_title, attempt_content, metrics, errors):
    """Выводит метрики в консоль в читаемом формате"""
    print("\n" + "="*80)
    print(f"Задание: {task_title}")
    print(f"Текст попытки: {attempt_content}")
    print("-"*80)
    print("Метрики:")
    print(f"Расстояние Левенштейна: {metrics.levenshtein}")
    print(f"WER (Word Error Rate): {metrics.wer:.2%}")
    print(f"CER (Character Error Rate): {metrics.cer:.2%}")
    print(f"PER (Position Error Rate): {metrics.per:.2%}")
    print(f"Точность: {metrics.accuracy:.2%}")
    print("-"*80)
    print("Количество ошибок по типам:")
    print(f"Орфографические ошибки: {metrics.word_error_count}")
    print(f"Пунктуационные ошибки: {metrics.punctuation_error_count}")
    print(f"Пропущенные слова: {metrics.missing_word_count}")
    print("-"*80)
    print("Найденные ошибки:")
    for error in errors:
        print(f"- {error.get_error_type_display()}: '{error.true_variant}'")
    print("="*80 + "\n")

def create_test_data():
    # Создаем тестовых пользователей
    teacher = User.objects.create(
        username="teacher",
        email="teacher@example.com",
        login="teacher",
        password="teacher123",
        first_name="Иван",
        last_name="Петров",
        role="teacher"
    )
    
    student = User.objects.create(
        username="student",
        email="student@example.com",
        login="student",
        password="student123",
        first_name="Анна",
        last_name="Сидорова",
        role="student"
    )

    # Создаем задания разной сложности
    tasks = [
        # Легкие задания
        {
            "title": "Простое предложение",
            "content": "Кошка спит на диване.",
            "text_complexity": "narrative",
            "difficulty": "easy",
            "min_words": 3,
            "max_words": 5,
            "min_sentences": 1,
            "max_sentences": 1
        },
        {
            "title": "Два простых предложения",
            "content": "Солнце светит ярко. Птицы поют в саду.",
            "text_complexity": "narrative",
            "difficulty": "easy",
            "min_words": 6,
            "max_words": 8,
            "min_sentences": 2,
            "max_sentences": 2
        },
        
        # Средние задания
        {
            "title": "Описание природы",
            "content": "В лесу растут высокие сосны. Между деревьями бегают белки. Воздух наполнен запахом хвои.",
            "text_complexity": "narrative",
            "difficulty": "medium",
            "min_words": 12,
            "max_words": 15,
            "min_sentences": 3,
            "max_sentences": 3
        },
        {
            "title": "Научный текст",
            "content": "Вода является важным химическим соединением. Она состоит из двух атомов водорода и одного атома кислорода. Вода может находиться в трех состояниях: жидком, твердом и газообразном.",
            "text_complexity": "scientific",
            "difficulty": "medium",
            "min_words": 20,
            "max_words": 25,
            "min_sentences": 3,
            "max_sentences": 3
        },
        
        # Сложные задания
        {
            "title": "Художественный текст",
            "content": "Осенний ветер кружил золотые листья в воздухе, создавая причудливые узоры. Старый дуб, стоявший на краю поляны, сбрасывал свою листву, словно готовясь к долгому зимнему сну. Вдалеке слышался шум реки, несущей свои воды к далекому морю.",
            "text_complexity": "artistic",
            "difficulty": "hard",
            "min_words": 30,
            "max_words": 35,
            "min_sentences": 3,
            "max_sentences": 3
        },
        {
            "title": "Технический текст",
            "content": "Квантовые компьютеры используют принципы квантовой механики для обработки информации. В отличие от классических компьютеров, которые работают с битами, квантовые компьютеры используют кубиты. Это позволяет им выполнять определенные вычисления значительно быстрее.",
            "text_complexity": "technical",
            "difficulty": "hard",
            "min_words": 25,
            "max_words": 30,
            "min_sentences": 3,
            "max_sentences": 3
        }
    ]

    print("\nНачинаем создание тестовых данных...")
    print("="*80)

    # Создаем задания и попытки
    for task_data in tasks:
        task = Task.objects.create(
            title=task_data["title"],
            content=task_data["content"],
            text_complexity=task_data["text_complexity"],
            status="active",
            difficulty=task_data["difficulty"],
            length=len(task_data["content"]),
            min_words=task_data["min_words"],
            max_words=task_data["max_words"],
            min_sentences=task_data["min_sentences"],
            max_sentences=task_data["max_sentences"],
            user=student,
            teacher=teacher
        )

        print(f"\nСоздано задание: {task.title} (сложность: {task.get_difficulty_display()})")
        print(f"Оригинальный текст: {task.content}")

        # Создаем попытки с разными типами ошибок
        attempt_types = [
            "Идеальная попытка",
            "Попытка с орфографическими ошибками",
            "Попытка с грамматическими ошибками",
            "Попытка с пропущенными словами",
            "Попытка с пунктуационными ошибками"
        ]
        
        attempts = [
            # Идеальная попытка
            task_data["content"],
            
            # Попытка с орфографическими ошибками
            task_data["content"].replace("а", "о").replace("е", "и"),
            
            # Попытка с грамматическими ошибками
            task_data["content"].replace("ет", "ют").replace("ит", "ят"),
            
            # Попытка с пропущенными словами
            " ".join(task_data["content"].split()[:-2]),
            
            # Попытка с пунктуационными ошибками
            task_data["content"].replace(".", ",").replace("!", ".")
        ]

        for attempt_type, attempt_content in zip(attempt_types, attempts):
            print(f"\n{attempt_type}:")
            attempt = Attempt.objects.create(
                task=task,
                content=attempt_content,
                stage="submitted"
            )
            
            # Анализируем ошибки и рассчитываем метрики
            errors = analyze_errors(attempt)
            metrics = calculate_metrics(attempt)
            
            # Выводим метрики в консоль
            print_metrics(task.title, attempt_content, metrics, errors)

    print("\nТестовые данные успешно созданы!")
    print("="*80)

if __name__ == "__main__":
    create_test_data() 