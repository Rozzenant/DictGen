import logging
import logging.config
import os

class ColoredFormatter(logging.Formatter):
    """Форматтер для цветного вывода логов"""
    
    COLORS = {
        'DEBUG': '\033[37m',     # Серый
        'INFO': '\033[32m',      # Зеленый
        'WARNING': '\033[33m',   # Желтый
        'ERROR': '\033[31m',     # Красный
        'CRITICAL': '\033[41m',  # Красный фон
    }
    RESET = '\033[0m'
    
    def formatMessage(self, record):
        """
        Форматирует сообщение с цветом.
        Этот метод вызывается из format() после установки всех атрибутов record.
        """
        color = self.COLORS.get(record.levelname, '')
        if color:
            # Применяем цвет ко всему сообщению
            return color + self._style.format(record) + self.RESET
        return self._style.format(record)

def setup_logging():
    """Настройка логирования для всего проекта"""
    
    # Создаем директорию для логов если её нет
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    config = {
        'version': 1,
        'disable_existing_loggers': True,  # Отключаем существующие логгеры
        'formatters': {
            'colored': {
                '()': ColoredFormatter,
                'format': '[ %(levelname)s ]: %(asctime)s.%(msecs)03d: %(name)s: %(message)s',
                'datefmt': '%H:%M:%S'
            },
            'detailed': {
                'format': '[ %(levelname)s ]: %(asctime)s.%(msecs)03d: %(name)s: %(message)s',
                'datefmt': '%H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
                'level': 'INFO'
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(log_dir, 'dictgen.log'),
                'formatter': 'detailed',
                'level': 'INFO'
            }
        },
        'root': {  # Корневой логгер
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {  # Логгер Django
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            'django.server': {  # Логгер Django сервера
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            'django.request': {  # Логгер Django запросов
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            'main': {  # Логгер нашего приложения
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    # Применяем конфигурацию
    logging.config.dictConfig(config) 