"""
Загрузчик издательств из JSON файла
"""
import json
from pathlib import Path


def load_publishers_from_json(json_path: Path = None) -> list[dict]:
    """
    Загружает издательства из JSON файла и преобразует в формат для создания Publisher
    
    Args:
        json_path: Путь к JSON файлу. Если None, использует дефолтный путь.
    
    Returns:
        Список словарей с данными издательств:
        {
            'name': str,
            'city': str,
            'website': str or None,
            'description': str
        }
    """
    if json_path is None:
        # Определяем путь относительно корня проекта
        base_dir = Path(__file__).parent.parent.parent
        json_path = base_dir / 'test_data_factory' / 'data' / 'russian_publishers_unified.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    publishers = []
    for item in data:
        publisher = {
            'name': item.get('Название', '').strip(),
            'city': item.get('Город', '').strip(),
            'website': item.get('ссылка на сайт') if item.get('ссылка на сайт') else '',
            'description': item.get('Описание', '').strip(),
        }
        
        # Пропускаем пустые названия
        if publisher['name']:
            publishers.append(publisher)
    
    return publishers


if __name__ == '__main__':
    # Тест
    publishers = load_publishers_from_json()
    print(f"Загружено издательств: {len(publishers)}")
    print("\nПервые 3:")
    for pub in publishers[:3]:
        print(f"  - {pub['name']} ({pub['city']})")

