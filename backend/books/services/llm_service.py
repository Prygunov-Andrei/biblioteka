"""
Сервис для работы с OpenAI GPT-4o API
Автозаполнение данных книги на основе изображений страниц
"""
import json
import os
import time
import base64
import requests
from pathlib import Path
from django.conf import settings
from typing import Dict, List, Optional, Any


def load_categories_json() -> Dict:
    """
    Загружает категории из базы данных с их ID для передачи в LLM
    
    Returns:
        dict: Словарь с категориями в формате {"categories": [{"id": ..., "code": ..., "name": ..., ...}]}
    """
    # Импортируем модель только здесь, чтобы избежать циклических импортов
    from books.models import Category
    
    # Загружаем все категории из БД с их ID
    categories = Category.objects.all().order_by('order', 'name')
    
    # Преобразуем в упрощенный список словарей - только id и name для лучшей читаемости LLM
    categories_list = []
    for cat in categories:
        # Упрощенный формат: только id и name, с указанием родительской категории если есть
        if cat.parent_category:
            category_dict = {
                "id": cat.id,
                "name": f"{cat.parent_category.name} → {cat.name}"  # Иерархия в названии
            }
        else:
            category_dict = {
                "id": cat.id,
                "name": cat.name
            }
        categories_list.append(category_dict)
    
    return {"categories": categories_list}


def encode_image_to_base64(image_path: str) -> str:
    """
    Кодирует изображение в base64 для отправки в OpenAI API
    
    Args:
        image_path: Путь к изображению (может быть URL или локальный путь)
    
    Returns:
        str: Base64 строка изображения
    """
    # Если это полный URL, скачиваем изображение
    if image_path.startswith('http://') or image_path.startswith('https://'):
        response = requests.get(image_path, timeout=30)
        response.raise_for_status()
        image_data = response.content
    elif image_path.startswith('/media/'):
        # Относительный путь от MEDIA_ROOT
        relative_path = image_path.replace('/media/', '')
        full_path = Path(settings.MEDIA_ROOT) / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Изображение не найдено: {full_path}")
        with open(full_path, 'rb') as f:
            image_data = f.read()
    else:
        # Пробуем как абсолютный путь
        full_path = Path(image_path)
        if not full_path.exists():
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")
        with open(full_path, 'rb') as f:
            image_data = f.read()
    
    return base64.b64encode(image_data).decode('utf-8')


def build_prompt(categories_json: Dict) -> str:
    """
    Строит промпт для LLM на основе шаблона из плана
    
    Args:
        categories_json: JSON с категориями
    
    Returns:
        str: Промпт для LLM
    """
    categories_str = json.dumps(categories_json, ensure_ascii=False, indent=2)
    
    prompt = f"""Ты - эксперт по анализу книг и классификации литературы. Проанализируй предоставленные изображения страниц книги и извлеки ВСЮ возможную информацию.

ШАГ 1: СНАЧАЛА ПРОАНАЛИЗИРУЙ КНИГУ
Внимательно изучи изображения страниц книги. Определи:
- Название книги
- Авторов
- Тематику и содержание
- Жанр (художественная литература, научная, учебная, детская, историческая, психология и т.д.)
- Целевую аудиторию

ШАГ 2: ОПРЕДЕЛИ КАТЕГОРИЮ
На основе анализа книги определи, к какой категории она относится. Используй свой экспертный опыт в классификации литературы.

ДОСТУПНЫЕ КАТЕГОРИИ (используй поле "id" для category_id):
{categories_str}

ВАЖНО ДЛЯ ВЫБОРА КАТЕГОРИИ:
- Каждая категория имеет поле "id" (это ЧИСЛО) - именно это число используй в category_id
- Каждая категория имеет поле "name" (название на русском) - используй его для поиска подходящей категории
- Стрелка "→" в названии означает иерархию (родительская → дочерняя категория)
- Пример: если выбрал категорию с name="Психология → Детская психология" и id=150, то category_id = 150

ЗАДАЧА - извлечь ВСЕ доступные данные о книге:
1. Название книги (title) - ОБЯЗАТЕЛЬНО, даже если неполное
2. Второе название/подзаголовок (subtitle) - перевод, серия, редакторы, иллюстраторы, произведения в издании
3. Авторы (authors) - массив имен авторов (до 3 авторов)
4. Издательство (publisher_name) - полное название издательства
5. Место издания (publication_place) - город
6. Год издания (year) - точный год, если виден
7. Год издания приблизительно (year_approx) - если год неполный: "197?", "18??", "19??"
8. Рубрика (category_id) - КРИТИЧЕСКИ ВАЖНО: 
   Сначала определи тематику книги (психология, художественная литература, история, детская литература и т.д.).
   Затем найди наиболее подходящую категорию в списке выше, сравнивая тематику книги с названиями категорий.
   Используй поле "id" (число) из выбранной категории.
   Если категория точно не подходит - верни null, НЕ выбирай случайную категорию.
9. Язык текста (language_name) - полное название языка: "Русский", "Английский", "Немецкий" и т.д.
10. Страниц (pages_info) - количество страниц, иллюстраций, схем, карт
11. Тираж (circulation) - количество экземпляров
12. Тип переплёта (binding_type) - один из вариантов
13. Детали переплёта (binding_details) - цвет, качество переплета
14. Формат книги (format) - один из вариантов
15. Состояние (condition) - один из вариантов
16. Детали состояния (condition_details) - изъяны, отсутствие страниц, загрязнения и т.д.
17. Содержание/аннотация (description) - ПОЛНОЕ описание содержания книги. Извлеки ВСЮ доступную информацию о содержании, аннотацию, оглавление, краткое содержание. НЕ ОБРЕЗАЙ текст - верни полное описание, даже если оно длинное.
18. ISBN (isbn) - если есть на обложке или титульном листе

ВАЖНЫЕ ПРАВИЛА:
- Если информация НЕ найдена на изображениях или ты НЕ УВЕРЕН - верни null для этого поля
- null интерпретируется как "Не определено"
- Для category_id (Рубрика) - АЛГОРИТМ ВЫБОРА:
  1. Проанализируй книгу: название, авторов, описание содержания, тематику
  2. Определи основную тематику (психология, художественная литература, история, детская литература, наука, образование и т.д.)
  3. Просмотри список категорий выше и найди категорию, название которой наиболее точно соответствует тематике книги
  4. Используй поле "id" (число) из найденной категории
  5. Если не уверен или не нашел подходящую категорию - верни null
  6. НЕ выбирай категорию наугад, лучше верни null
- Для binding_type используй ТОЛЬКО: paper, selfmade, cardboard, hard, fabric, owner, halfleather, composite, leather
- Для format используй ТОЛЬКО: very_large, encyclopedic, increased, regular, reduced, miniature
- Для condition используй ТОЛЬКО: ideal, excellent, good, satisfactory, poor
- Для language_name используй полное название языка на русском: "Русский", "Английский", "Немецкий", "Французский" и т.д.
- Авторов может не быть (массив может быть пустым [])
- Год издания: если виден полный год - используй year (integer), если неполный - используй year_approx (string)
- Если год вообще не виден - оба поля null
- pages_info может содержать: "256 стр.", "320 стр., 16 иллюстраций", "480 стр., схемы, карты" и т.д.
- binding_details может содержать: "Синий, тканевый", "Коричневый, кожаный" и т.д.
- condition_details может содержать: "Отсутствуют страницы 5-8", "Загрязнения на обложке", "Рассыпанный блок" и т.д.

ВЕРНИ ОТВЕТ СТРОГО В ФОРМАТЕ JSON согласно схеме:
{{
  "title": string (ОБЯЗАТЕЛЬНО, минимум 1 символ),
  "subtitle": string или null,
  "category_id": integer или null (ОБЯЗАТЕЛЬНО используй поле "id" из категории, это число, НЕ "code" и НЕ "slug"),
  "authors": array of strings или [],
  "publisher_name": string или null,
  "publication_place": string или null,
  "year": integer или null,
  "year_approx": string или null,
  "pages_info": string или null,
  "circulation": integer или null,
  "language_name": string или null,
  "binding_type": string или null,
  "binding_details": string или null,
  "format": string или null,
  "condition": string или null,
  "condition_details": string или null,
  "isbn": string или null,
  "description": string или null
}}

ВАЖНО: 
- Верни ВСЕ поля, даже если значение null. Не пропускай поля в JSON ответе.
- Для поля description (Содержание/Аннотация) верни ПОЛНЫЙ текст, не обрезай его. Если аннотация длинная - верни её полностью.
- max_tokens установлен достаточно высоким (8000), чтобы вместить полное описание."""
    
    return prompt


def auto_fill_book_data(image_urls: List[str], max_retries: int = 3) -> Dict[str, Any]:
    """
    Отправляет изображения и категории в OpenAI GPT-4o
    и получает структурированные данные о книге
    
    Args:
        image_urls: Список URL нормализованных изображений
        max_retries: Максимальное количество попыток при ошибке
    
    Returns:
        dict: Словарь с данными книги и метаданными:
            {
                "success": bool,
                "data": {...},  # Данные книги
                "error": str или None,
                "confidence": float (опционально)
            }
    
    Raises:
        ValueError: Если не указан API ключ OpenAI
        requests.RequestException: При ошибках сети
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
    
    # Загружаем категории
    try:
        categories_data = load_categories_json()
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Ошибка загрузки категорий: {str(e)}",
            "confidence": None
        }
    
    # Строим промпт
    prompt = build_prompt(categories_data)
    
    # Подготавливаем изображения для API
    image_contents = []
    import sys
    for url in image_urls[:10]:  # OpenAI API поддерживает до 10 изображений
        try:
            print(f"🔵 Обработка изображения: {url}", file=sys.stderr)
            sys.stderr.flush()
            
            # Всегда кодируем в base64, так как OpenAI не может получить доступ к localhost
            # Если это полный URL (http://localhost:8000/media/...), загружаем и кодируем
            if url.startswith('http://localhost') or url.startswith('http://127.0.0.1'):
                # Локальный URL - загружаем и кодируем в base64
                print(f"🔵 Локальный URL обнаружен, кодируем в base64...", file=sys.stderr)
                sys.stderr.flush()
                base64_image = encode_image_to_base64(url)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            elif url.startswith('http://') or url.startswith('https://'):
                # Внешний URL - используем напрямую (если OpenAI может получить доступ)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                })
            else:
                # Локальный путь - кодируем в base64
                base64_image = encode_image_to_base64(url)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            print(f"✓ Изображение обработано успешно", file=sys.stderr)
            sys.stderr.flush()
        except Exception as e:
            import traceback
            print(f"⚠️ Ошибка обработки изображения {url}: {e}", file=sys.stderr)
            print(f"⚠️ Traceback: {traceback.format_exc()}", file=sys.stderr)
            sys.stderr.flush()
            continue
    
    if not image_contents:
        return {
            "success": False,
            "data": None,
            "error": "Не удалось обработать ни одного изображения",
            "confidence": None
        }
    
    # Формируем сообщения для API
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                *image_contents
            ]
        }
    ]
    
    # Параметры запроса
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 8000,  # Увеличено для полного описания книги
        "temperature": 0.3,  # Низкая температура для более точных результатов
        "response_format": {"type": "json_object"}  # JSON mode
    }
    
    # Выполняем запрос с retry механизмом
    last_error = None
    import sys
    for attempt in range(max_retries):
        try:
            print(f"🔵 Отправка запроса в OpenAI API (попытка {attempt + 1}/{max_retries})...", file=sys.stderr)
            sys.stderr.flush()
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"🔵 Ответ от OpenAI API: статус {response.status_code}", file=sys.stderr)
            sys.stderr.flush()
            
            response.raise_for_status()
            
            result = response.json()
            
            # Извлекаем ответ
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                # Парсим JSON ответ
                try:
                    book_data = json.loads(content)
                    
                    # Валидация обязательных полей
                    if 'title' not in book_data or not book_data.get('title'):
                        return {
                            "success": False,
                            "data": None,
                            "error": "LLM не смог определить название книги",
                            "confidence": None
                        }
                    
                    # Нормализация данных: заменяем пустые строки на null для полей, которые могут быть null
                    nullable_fields = [
                        'subtitle', 'publisher_name', 'publication_place', 'year_approx',
                        'pages_info', 'language_name', 'binding_type', 'binding_details',
                        'format', 'condition', 'condition_details', 'isbn', 'description'
                    ]
                    for field in nullable_fields:
                        if field in book_data and book_data[field] == '':
                            book_data[field] = None
                    
                    # Нормализация числовых полей
                    if 'year' in book_data and book_data['year'] == '':
                        book_data['year'] = None
                    if 'circulation' in book_data and book_data['circulation'] == '':
                        book_data['circulation'] = None
                    if 'category_id' in book_data and book_data['category_id'] == '':
                        book_data['category_id'] = None
                    
                    # Нормализация массива авторов
                    if 'authors' not in book_data:
                        book_data['authors'] = []
                    elif not isinstance(book_data['authors'], list):
                        # Если пришла строка, разбиваем по запятым
                        if isinstance(book_data['authors'], str):
                            book_data['authors'] = [a.strip() for a in book_data['authors'].split(',') if a.strip()]
                        else:
                            book_data['authors'] = []
                    
                    # Вычисляем confidence на основе заполненных полей
                    filled_fields = sum(1 for k, v in book_data.items() if v is not None and v != "")
                    total_fields = len(book_data)
                    confidence = filled_fields / total_fields if total_fields > 0 else 0.0
                    
                    print(f"✓ Успешно получены данные от LLM (confidence: {confidence:.2f})", file=sys.stderr)
                    sys.stderr.flush()
                    
                    return {
                        "success": True,
                        "data": book_data,
                        "error": None,
                        "confidence": confidence
                    }
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Ошибка парсинга JSON ответа от LLM: {str(e)}"
                    print(f"⚠️ {error_msg}", file=sys.stderr)
                    print(f"⚠️ Ответ LLM: {content[:500]}", file=sys.stderr)
                    sys.stderr.flush()
                    last_error = error_msg
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return {
                            "success": False,
                            "data": None,
                            "error": error_msg,
                            "confidence": None
                        }
            else:
                error_msg = "Неожиданный формат ответа от OpenAI API"
                print(f"⚠️ {error_msg}: {result}", file=sys.stderr)
                sys.stderr.flush()
                last_error = error_msg
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return {
                        "success": False,
                        "data": None,
                        "error": error_msg,
                        "confidence": None
                    }
                    
        except requests.exceptions.Timeout:
            error_msg = "Таймаут запроса к OpenAI API"
            print(f"⚠️ {error_msg}", file=sys.stderr)
            sys.stderr.flush()
            last_error = error_msg
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": error_msg,
                    "confidence": None
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка запроса к OpenAI API: {str(e)}"
            print(f"⚠️ {error_msg}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"⚠️ Детали ошибки: {error_detail}", file=sys.stderr)
                    
                    # Специальная обработка ошибки "unsupported_country_region_territory"
                    if 'error' in error_detail and isinstance(error_detail['error'], dict):
                        error_code = error_detail['error'].get('code', '')
                        if error_code == 'unsupported_country_region_territory':
                            error_msg = "OpenAI API недоступен в вашем регионе. Используйте VPN или обратитесь в поддержку OpenAI."
                except:
                    print(f"⚠️ Текст ответа: {e.response.text[:500]}", file=sys.stderr)
            sys.stderr.flush()
            last_error = error_msg
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": error_msg,
                    "confidence": None
                }
    
    return {
        "success": False,
        "data": None,
        "error": f"Не удалось получить ответ после {max_retries} попыток. Последняя ошибка: {last_error}",
        "confidence": None
    }

