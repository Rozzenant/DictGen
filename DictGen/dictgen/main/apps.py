from django.apps import AppConfig
import logging
import os
import torch
from .logger import setup_logging

# Инициализируем логирование при импорте
logger = logging.getLogger(__name__)
setup_logging()

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        """Инициализация приложения"""
        try:
            # Проверяем CUDA
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                device_count = torch.cuda.device_count()
                logger.info(f"CUDA доступна. Найдено GPU устройств: {device_count}")
                for i in range(device_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
                    logger.info(f"GPU {i}: {gpu_name}, Память: {gpu_mem:.1f}GB")
            else:
                logger.warning("CUDA недоступна. Будет использован CPU.")

            # Используем существующую директорию для кэша модели
            cache_dir = "S:/diplom_model/cache"
            if not os.path.exists(cache_dir):
                logger.error(f"Директория кэша {cache_dir} не найдена!")
                raise FileNotFoundError(f"Директория кэша {cache_dir} не найдена!")
            
            # Устанавливаем переменные окружения
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            os.environ["TRANSFORMERS_CACHE"] = cache_dir
            
            # Загружаем генератор текста
            from .llm_generator import get_generator
            generator = get_generator()
            logger.info("Приложение успешно инициализировано")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {str(e)}")
            raise
