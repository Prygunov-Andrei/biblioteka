"""
Загрузчик авторов из JSON файла
"""
import json
from pathlib import Path


def load_authors_from_json(json_path: Path = None) -> list[dict]:
    """
    Загружает авторов из JSON файла и преобразует в формат для создания Author
    
    Args:
        json_path: Путь к JSON файлу. Если None, использует дефолтный путь.
    
    Returns:
        Список словарей с данными авторов:
        {
            'full_name': str,  # Фамилия Имя Отчество
            'birth_year': int or None,
            'death_year': int or None,
            'biography': str
        }
    """
    if json_path is None:
        # Определяем путь относительно корня проекта
        base_dir = Path(__file__).parent.parent.parent
        # Пробуем сначала новый файл, потом старый для обратной совместимости
        new_path = base_dir / 'test_data_factory' / 'data' / 'russian_authors_full_merged.json'
        old_path = base_dir / 'test_data_factory' / 'data' / 'russian_authors_batch1_structured.json'
        json_path = new_path if new_path.exists() else old_path
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    authors = []
    for item in data:
        surname = item.get('Фамилия', '').strip()
        name = item.get('Имя', '').strip()
        patronymic = item.get('Отчество')
        
        # Формируем полное имя
        parts = [surname, name]
        if patronymic:
            parts.append(patronymic.strip())
        full_name = ' '.join(parts).strip()
        
        # Пропускаем пустые имена
        if not full_name:
            continue
        
        author = {
            'full_name': full_name,
            'birth_year': item.get('год рождения'),
            'death_year': item.get('год смерти'),
            'biography': item.get('короткая биография', '').strip(),
        }
        
        authors.append(author)
    
    return authors


if __name__ == '__main__':
    # Тест
    authors = load_authors_from_json()
    print(f"Загружено авторов: {len(authors)}")
    print("\nПервые 3:")
    for author in authors[:3]:
        print(f"  - {author['full_name']} ({author['birth_year']}-{author['death_year']})")

