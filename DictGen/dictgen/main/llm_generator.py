import os
import logging
import requests
import hashlib
import json
from tqdm import tqdm
from typing import List, Optional, Dict
from ctransformers import AutoModelForCausalLM
from dotenv import load_dotenv
from openai import OpenAI
from .models import Term

# Используем общий логгер
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()

class TextGenerator:
    def __init__(self):
        self.model = None
        self.repo_id = "TheBloke/Llama-2-7B-Chat-GGUF"
        self.model_file = "llama-2-7b-chat.Q4_K_M.gguf"
        self.model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
        self.cache_dir = "S:/diplom_model/cache"
        
        # Конфигурация BotHub API
        self.use_bothub = False
        self.bothub_api_key = os.getenv('BOTHUB_API_KEY')
        self.bothub_model = "gpt-4o-mini"
        
        # Инициализация OpenAI клиента для BotHub
        if self.bothub_api_key:
            self.bothub_client = OpenAI(
                api_key=self.bothub_api_key,
                base_url='https://bothub.chat/api/v2/openai/v1'
            )
            self.use_bothub = True
            logger.info("BotHub API настроен и будет использоваться как основной метод генерации")
        else:
            logger.warning("Ключ BotHub API не найден в файле .env, используем локальную модель")
            # Загружаем модель
            self._load_model()
        
    def _download_model(self) -> str:
        """Скачивание модели"""
        try:
            logger.info(f"Скачивание модели {self.model_file}")
            
            # Путь для сохранения модели
            model_path = os.path.join(self.cache_dir, self.model_file)
            
            # Удаляем файл если он существует
            if os.path.exists(model_path):
                os.remove(model_path)
            
            # Скачиваем модель
            response = requests.get(self.model_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(model_path, 'wb') as file, tqdm(
                desc=self.model_file,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as progress_bar:
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    progress_bar.update(size)
                    
            logger.info(f"Модель успешно скачана в {model_path}")
            
            # Проверяем размер файла
            if os.path.getsize(model_path) != total_size:
                raise ValueError(f"Размер скачанного файла ({os.path.getsize(model_path)}) не соответствует ожидаемому ({total_size})")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Ошибка при скачивании модели: {str(e)}")
            # Удаляем поврежденный файл
            if os.path.exists(model_path):
                os.remove(model_path)
            raise
    
    def _load_model(self) -> None:
        """Загрузка модели"""
        try:
            logger.info(f"Загрузка модели {self.repo_id}")
            
            # Путь к файлу модели
            model_path = os.path.join(self.cache_dir, self.model_file)
            
            # Если модель не существует или повреждена - скачиваем
            if not os.path.exists(model_path):
                logger.info(f"Модель не найдена в {model_path}")
                model_path = self._download_model()
            
            # Загружаем модель
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path_or_repo_id=model_path,
                model_type="llama",
                gpu_layers=0,  # CPU режим
                context_length=2048,
                batch_size=1,
                threads=8  # Используем 8 потоков CPU
            )
            
            logger.info("Модель успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {str(e)}")
            # При ошибке загрузки удаляем файл и пробуем скачать заново
            if os.path.exists(model_path):
                os.remove(model_path)
                logger.info("Удален поврежденный файл модели, попытка повторной загрузки")
                model_path = self._download_model()
                self._load_model()  # Рекурсивно пробуем загрузить модель
            else:
                raise
    
    def _create_prompt(self, terms: List[Term]) -> str:
        """Создание промпта для генерации"""
        terms_str = ", ".join(t.content for t in terms)
        return f"""[INST] Прочитайте фрагмент лекции, объясняющий следующие термины: {terms_str}

Требования к лекции:
1. Объем: 3-6 предложений
2. Найдите наиболее логичную тематическую связь между этими терминами и постройте лекцию вокруг этой темы
3. Объясните, как эти термины взаимодействуют или влияют друг на друга в рамках выбранной темы
4. Каждый термин должен естественно вытекать из контекста предыдущего
5. Используйте причинно-следственные связи для объяснения взаимосвязи терминов
6. Завершите фрагмент выводом, подчеркивающим связь между терминами

Пожалуйста, начните лекцию сразу, без вступительных фраз. [/INST]"""
    
    def _process_text(self, text: str) -> str:
        """Базовая обработка сгенерированного текста"""
        # Убираем лишние пробелы
        text = " ".join(text.split())
        
        # Очищаем от служебных токенов
        text = text.replace("<s>", "").replace("</s>", "").strip()
        text = text.replace("[INST]", "").replace("[/INST]", "").strip()
        
        # Делаем первую букву заглавной
        text = text[0].upper() + text[1:] if text else text
        
        # Добавляем точку в конце, если её нет
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
            
        return text
    
    def _verify_text(self, text: str, terms: List[Term]) -> bool:
        """Проверка текста на соответствие требованиям"""
        # Проверяем количество предложений
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) < 3:
            logger.warning(f"Мало предложений: {len(sentences)}")
            return False
        
        # Проверяем использование всех терминов
        text_lower = text.lower()
        unused_terms = [t.content for t in terms if t.content.lower() not in text_lower]
        if unused_terms:
            logger.warning(f"Не использованы термины: {unused_terms}")
            return False
            
        return True
    
    def _generate_with_bothub(self, terms: List[Term]) -> Optional[str]:
        """Генерация текста с использованием BotHub API"""
        try:
            # Создаем промпт
            prompt = self._create_prompt(terms)
            
            # Создаем сообщения для чата
            messages = [
                {
                    'role': 'system',
                    'content': '''Ты - опытный преподаватель в университете, читающий лекцию студентам.
Твой стиль:
0. Говоришь как любой преподаватель в университете, иногда используя ненаучные термины, запинаешься, не говоришь сразу, добавляешь слова-паразиты.
1. Говоришь четко и структурированно
2. Используешь академический стиль речи, но доступно объясняешь сложные термины
3. Приводишь практические примеры для лучшего понимания
4. Периодически обращаешься к аудитории ("обратите внимание", "давайте рассмотрим", "как вы можете видеть")
5. Делаешь логические связки между частями материала
6. В конце подводишь итог рассмотренной темы

Веди лекцию так, как будто ты стоишь перед аудиторией студентов.'''
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Запускаем потоковую генерацию
            stream = self.bothub_client.chat.completions.create(
                model=self.bothub_model,
                messages=messages,
                temperature=0.8,
                max_tokens=512,
                top_p=0.9,
                stream=True
            )
            
            # Собираем текст из потока
            generated_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    generated_text += chunk.choices[0].delta.content
            
            # Обрабатываем полученный текст
            processed_text = self._process_text(generated_text)
            
            # Проверяем результат
            if self._verify_text(processed_text, terms):
                return processed_text
            
            logger.warning("Сгенерированный текст не прошел проверку")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при использовании BotHub API: {str(e)}")
            return None

    def generate(self, terms: List[Term]) -> str:
        """Генерация текста с использованием заданных терминов"""
        if not terms:
            return "Не указаны термины для генерации"
            
        # Пробуем сначала использовать BotHub API
        if self.use_bothub:
            logger.info("Попытка генерации через BotHub API")
            result = self._generate_with_bothub(terms)
            if result:
                return result
            logger.warning("Генерация через BotHub API не удалась, переключаемся на локальную модель")
        
        # Если BotHub недоступен или не удалось сгенерировать текст, используем локальную модель
        if not self.model:
            self._load_model()
            
        try:
            # Создаем промпт
            prompt = self._create_prompt(terms)
            logger.info(f"Генерация текста для терминов: {[t.content for t in terms]}")
            logger.debug(f"Промпт: {prompt}")
            
            # Генерируем текст
            logger.info("Запуск генерации...")
            generated_text = self.model(
                prompt,
                max_new_tokens=512,
                temperature=0.8,
                top_k=40,
                top_p=0.9,
                repetition_penalty=1.15,
                stop=["</s>", "[INST]", "[/INST]"]
            )
            
            # Обрабатываем текст
            processed_text = self._process_text(generated_text)
            
            # Проверяем результат
            if not self._verify_text(processed_text, terms):
                logger.warning("Текст не прошел проверку, пробуем еще раз")
                return self.generate(terms)  # Пробуем ещё раз
                
            logger.info("Генерация успешно завершена")
            logger.debug(f"Сгенерированный текст: {processed_text}")
            return processed_text
            
        except Exception as e:
            error_msg = f"Ошибка при генерации: {str(e)}"
            logger.error(error_msg)
            return error_msg

# Глобальный экземпляр генератора
_generator = None

def get_generator() -> TextGenerator:
    """Получение глобального экземпляра генератора"""
    global _generator
    if _generator is None:
        _generator = TextGenerator()
    return _generator
