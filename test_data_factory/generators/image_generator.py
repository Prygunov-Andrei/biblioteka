"""
Генератор изображений книг
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# Палитра цветов для однотонных изображений
COLOR_PALETTE = [
    (200, 180, 160),  # Бежевый
    (180, 200, 220),  # Голубой
    (220, 200, 180),  # Персиковый
    (200, 220, 200),  # Мятный
    (240, 220, 200),  # Кремовый
    (180, 180, 200),  # Лавандовый
    (220, 200, 220),  # Розовый
    (200, 220, 240),  # Небесный
    (240, 240, 220),  # Светло-желтый
    (200, 200, 200),  # Светло-серый
    (220, 240, 240),  # Бирюзовый
    (240, 230, 220),  # Песочный
]

# Темные цвета для текста
TEXT_COLORS = [
    (40, 40, 40),      # Темно-серый
    (60, 40, 40),      # Темно-коричневый
    (40, 40, 60),      # Темно-синий
    (50, 40, 40),      # Темно-бордовый
]


def generate_book_image(
    title: str,
    order: int,
    output_dir: Path,
    width: int = 800,
    height: int = 1200
) -> Path:
    """
    Генерирует изображение книги
    
    Args:
        title: Название книги (для главного изображения)
        order: Порядок изображения (1 - главное с текстом, 2-3 - однотонные)
        output_dir: Директория для сохранения
        width: Ширина изображения
        height: Высота изображения
    
    Returns:
        Path к созданному файлу изображения
    """
    # Создаем изображение
    img = Image.new('RGB', (width, height), color=random.choice(COLOR_PALETTE))
    draw = ImageDraw.Draw(img)
    
    # Для главного изображения (order=1) добавляем текст
    if order == 1 and title:
        try:
            # Пытаемся использовать стандартный шрифт
            # На macOS может быть другой путь
            font_size = 48
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    # Fallback на стандартный шрифт
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Разбиваем длинный заголовок на строки
        words = title.split()
        lines = []
        current_line = []
        max_chars_per_line = 20
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars_per_line:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Ограничиваем количество строк (максимум 5)
        lines = lines[:5]
        
        # Выбираем цвет текста (темный для контраста)
        text_color = random.choice(TEXT_COLORS)
        
        # Вычисляем позицию для текста (по центру)
        total_height = len(lines) * (font_size + 10)
        start_y = (height - total_height) // 2
        
        # Рисуем каждую строку
        for i, line in enumerate(lines):
            # Вычисляем ширину текста для центрирования
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = start_y + i * (font_size + 10)
            
            # Рисуем тень для лучшей читаемости (опционально)
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), line, 
                     font=font, fill=(0, 0, 0, 100))
            
            # Рисуем основной текст
            draw.text((x, y), line, font=font, fill=text_color)
    
    # Сохраняем изображение
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"book_image_{order}_{random.randint(1000, 9999)}.jpg"
    filepath = output_dir / filename
    
    # Сохраняем как JPEG
    img.save(filepath, 'JPEG', quality=85)
    
    return filepath


def generate_book_images(
    title: str,
    count: int,
    output_dir: Path
) -> list[Path]:
    """
    Генерирует несколько изображений для книги
    
    Args:
        title: Название книги
        count: Количество изображений (обычно 3)
        output_dir: Директория для сохранения
    
    Returns:
        Список путей к созданным файлам
    """
    images = []
    for order in range(1, count + 1):
        img_path = generate_book_image(title, order, output_dir)
        images.append(img_path)
    
    return images


if __name__ == '__main__':
    # Тест
    output_dir = Path(__file__).parent.parent / 'generated_images'
    title = "История русской литературы"
    
    print("Генерирую тестовые изображения...")
    images = generate_book_images(title, 3, output_dir)
    
    print(f"\nСоздано {len(images)} изображений:")
    for img_path in images:
        print(f"  - {img_path}")

