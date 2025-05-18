# Роли пользователя
USER_ROLES_CHOICES = [
    ('student', 'Ученик'),
    ('teacher', 'Преподаватель'),
    ('admin', 'Администратор'),
]

# Статусы задания
TASK_STATUS_CHOICES = [
    ('draft', 'Черновик'),
    ('active', 'Активное'),
    ('in_review', 'На проверке'),
    ('reviewed', 'Проверено'),
    ('completed', 'Завершено'),
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

ERROR_TYPES_CHOICES = [
    ('spelling', 'Орфографическая ошибка'),
    ('grammar', 'Грамматическая ошибка'),
    ('punctuation', 'Пунктуационная ошибка'),
    ('missing', 'Пропущенное слово'),
    ('extra', 'Лишнее слово'),
]