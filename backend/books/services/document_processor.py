"""
Сервис обработки документов
Использует OpenCV для обнаружения границ документа (без платных SDK)
"""
import cv2
import numpy as np
import uuid
import os
from pathlib import Path
from django.conf import settings


def order_points(pts):
    """Упорядочивает точки в порядке: верхний-левый, верхний-правый, нижний-правый, нижний-левый."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    """Применяет перспективное преобразование к изображению."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped


def detect_document_contour(image):
    """
    Обнаружение границ документа на изображении с помощью OpenCV
    
    Args:
        image: Изображение в формате OpenCV (numpy array)
    
    Returns:
        numpy array: Массив из 4 точек углов документа или None
    """
    import sys
    
    # Преобразуем в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Пробуем разные методы предобработки
    methods = [
        # Метод 1: Стандартный Canny
        {
            'name': 'Canny стандартный',
            'preprocess': lambda g: cv2.GaussianBlur(g, (5, 5), 0),
            'edges': lambda b: cv2.Canny(b, 50, 150)
        },
        # Метод 2: Адаптивная бинаризация + Canny
        {
            'name': 'Адаптивная бинаризация',
            'preprocess': lambda g: cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
            'edges': lambda b: cv2.Canny(b, 50, 150)
        },
        # Метод 3: Морфологические операции + Canny
        {
            'name': 'Морфология + Canny',
            'preprocess': lambda g: cv2.morphologyEx(cv2.GaussianBlur(g, (5, 5), 0), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)),
            'edges': lambda b: cv2.Canny(b, 30, 100)
        },
        # Метод 4: Более агрессивный Canny
        {
            'name': 'Canny агрессивный',
            'preprocess': lambda g: cv2.GaussianBlur(g, (7, 7), 0),
            'edges': lambda b: cv2.Canny(b, 20, 80)
        },
        # Метод 5: Sobel градиенты (для белых документов на белом фоне)
        {
            'name': 'Sobel градиенты',
            'preprocess': lambda g: cv2.GaussianBlur(g, (5, 5), 0),
            'edges': lambda b: cv2.Canny(cv2.convertScaleAbs(cv2.Sobel(b, cv2.CV_64F, 1, 1, ksize=3)), 30, 100)
        },
        # Метод 6: Laplacian (для белых документов)
        {
            'name': 'Laplacian',
            'preprocess': lambda g: cv2.GaussianBlur(g, (5, 5), 0),
            'edges': lambda b: cv2.Canny(cv2.convertScaleAbs(cv2.Laplacian(b, cv2.CV_64F)), 30, 100)
        },
        # Метод 7: Очень низкие пороги Canny (для белых документов)
        {
            'name': 'Canny низкие пороги',
            'preprocess': lambda g: cv2.GaussianBlur(g, (9, 9), 0),
            'edges': lambda b: cv2.Canny(b, 10, 30)
        },
    ]
    
    image_area = image.shape[0] * image.shape[1]
    min_area = image_area * 0.3   # Минимум 30% изображения - документ должен занимать большую часть
    max_area = image_area * 0.99   # Максимум 99% изображения
    
    for method in methods:
        try:
            print(f"🔍 Пробуем метод: {method['name']}", file=sys.stderr)
            sys.stderr.flush()
            
            # Предобработка
            processed = method['preprocess'](gray)
            # Детекция краев
            edged = method['edges'](processed)
            
            # Находим контуры
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                continue
            
            # Сортируем контуры по площади (от большего к меньшему)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]
            
            print(f"🔍 Найдено {len(contours)} контуров для анализа", file=sys.stderr)
            sys.stderr.flush()
            
            # Ищем контур, который похож на четырехугольник
            for i, contour in enumerate(contours):
                # Аппроксимируем контур
                peri = cv2.arcLength(contour, True)
                if peri < 100:  # Пропускаем слишком маленькие контуры
                    continue
                
                # Пробуем разные уровни аппроксимации
                for epsilon_factor in [0.01, 0.02, 0.03, 0.05]:
                    approx = cv2.approxPolyDP(contour, epsilon_factor * peri, True)
                    
                    # Если контур имеет 4 точки
                    if len(approx) == 4:
                        area = cv2.contourArea(approx)
                        area_percent = (area / image_area) * 100
                        
                        if min_area <= area <= max_area:
                            print(f"✓ Найден документ методом '{method['name']}': площадь {area:.0f} ({area_percent:.1f}% изображения)", file=sys.stderr)
                            sys.stderr.flush()
                            return approx.reshape(4, 2)
            
            # Если не нашли идеальный четырехугольник, пробуем более гибкую аппроксимацию
            for i, contour in enumerate(contours):
                peri = cv2.arcLength(contour, True)
                if peri < 100:
                    continue
                
                # Более гибкая аппроксимация
                approx = cv2.approxPolyDP(contour, 0.1 * peri, True)
                
                if len(approx) >= 4:
                    points = approx.reshape(-1, 2)
                    
                    if len(points) >= 4:
                        # Находим 4 крайние точки
                        s = points.sum(axis=1)
                        diff = np.diff(points, axis=1)
                        
                        top_left = points[np.argmin(s)]
                        bottom_right = points[np.argmax(s)]
                        top_right = points[np.argmin(diff)]
                        bottom_left = points[np.argmax(diff)]
                        
                        area = cv2.contourArea(np.array([top_left, top_right, bottom_right, bottom_left]))
                        area_percent = (area / image_area) * 100
                        
                        if min_area <= area <= max_area:
                            print(f"✓ Найден документ методом '{method['name']}' (гибкая): площадь {area:.0f} ({area_percent:.1f}% изображения)", file=sys.stderr)
                            sys.stderr.flush()
                            return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
        
        except Exception as e:
            print(f"⚠ Ошибка в методе '{method['name']}': {e}", file=sys.stderr)
            sys.stderr.flush()
            continue
    
    # Если ничего не помогло, пробуем найти самый большой контур и использовать его как документ
    print(f"🔍 Пробуем использовать самый большой контур...", file=sys.stderr)
    sys.stderr.flush()
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Берем самый большой контур
        largest_contour = max(contours, key=cv2.contourArea)
        peri = cv2.arcLength(largest_contour, True)
        
        # Пробуем разные уровни аппроксимации
        for epsilon_factor in [0.01, 0.02, 0.05, 0.1, 0.15]:
            approx = cv2.approxPolyDP(largest_contour, epsilon_factor * peri, True)
            
            if len(approx) >= 4:
                points = approx.reshape(-1, 2)
                if len(points) >= 4:
                    s = points.sum(axis=1)
                    diff = np.diff(points, axis=1)
                    
                    top_left = points[np.argmin(s)]
                    bottom_right = points[np.argmax(s)]
                    top_right = points[np.argmin(diff)]
                    bottom_left = points[np.argmax(diff)]
                    
                    area = cv2.contourArea(np.array([top_left, top_right, bottom_right, bottom_left]))
                    if area > image_area * 0.3:  # Должен занимать хотя бы 30% изображения
                        print(f"✓ Найден документ (самый большой контур): площадь {area:.0f} ({(area/image_area)*100:.1f}% изображения)", file=sys.stderr)
                        sys.stderr.flush()
                        return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    
    # Если все методы не сработали, пробуем использовать границы изображения с небольшим отступом
    # Это для случаев, когда документ занимает почти все изображение (белый документ на белом фоне)
    print(f"🔍 Пробуем использовать границы изображения (fallback для белых документов)...", file=sys.stderr)
    sys.stderr.flush()
    
    h, w = image.shape[:2]
    margin = min(w, h) * 0.05  # 5% отступ от краев
    
    # Если изображение достаточно большое и похоже на документ (высокое разрешение)
    if w > 2000 and h > 2000:
        pts = np.array([
            [margin, margin],           # верхний-левый
            [w - margin, margin],      # верхний-правый
            [w - margin, h - margin],  # нижний-правый
            [margin, h - margin]       # нижний-левый
        ], dtype=np.float32)
        
        area = cv2.contourArea(pts)
        if area > image_area * 0.8:  # Занимает больше 80% изображения
            print(f"✓ Используем границы изображения (fallback): площадь {area:.0f} ({(area/image_area)*100:.1f}% изображения)", file=sys.stderr)
            sys.stderr.flush()
            return pts
    
    return None


def process_document(input_path, output_path):
    """
    Обработка документа - нормализация перспективы
    Использует OpenCV для обнаружения границ (без платных SDK)
    
    Args:
        input_path: Путь к входному изображению (Path или str)
        output_path: Путь для сохранения обработанного изображения (Path или str)
    
    Returns:
        tuple: (width, height) размер обработанного изображения
    
    Raises:
        ValueError: Если не удалось загрузить изображение или найти документ
    """
    import sys
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    print(f"🔥 Обработка документа (OpenCV)", file=sys.stderr)
    print(f"📥 Input:  {input_path}", file=sys.stderr)
    print(f"📤 Output: {output_path}", file=sys.stderr)
    sys.stderr.flush()
    
    # Загружаем изображение
    image = cv2.imread(str(input_path))
    if image is None:
        raise ValueError(f"Не удалось загрузить изображение: {input_path}")
    
    orig_h, orig_w = image.shape[:2]
    print(f"📐 Исходный размер: {orig_w}x{orig_h}", file=sys.stderr)
    sys.stderr.flush()
    
    # Обнаружение границ документа с помощью OpenCV
    print(f"🔍 Обнаружение границ документа с помощью OpenCV...", file=sys.stderr)
    sys.stderr.flush()
    
    pts = detect_document_contour(image)
    
    if pts is None:
        raise ValueError("Документ не найден на изображении")
    
    print(f"📍 Координаты углов документа:", file=sys.stderr)
    for i, point in enumerate(pts):
        print(f"  Угол {i+1}: ({point[0]:.1f}, {point[1]:.1f})", file=sys.stderr)
    sys.stderr.flush()
    
    # Применяем перспективное преобразование
    normalized = four_point_transform(image, pts)
    
    new_h, new_w = normalized.shape[:2]
    print(f"✅ Финальный размер: {new_w}x{new_h}", file=sys.stderr)
    sys.stderr.flush()
    
    # Сохраняем результат
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), normalized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"💾 Сохранено: {output_path}", file=sys.stderr)
    print("🎉 Обработка завершена!", file=sys.stderr)
    sys.stderr.flush()
    
    return (new_w, new_h)


def normalize_pages_batch(files):
    """
    Пакетная нормализация страниц для мастера создания книги
    
    Args:
        files: Список загруженных файлов (InMemoryUploadedFile или TemporaryUploadedFile)
    
    Returns:
        list: Список словарей с информацией о нормализованных изображениях:
            {
                'id': str,  # Уникальный ID для временного файла
                'original_filename': str,
                'normalized_url': str,  # URL для доступа к нормализованному изображению
                'width': int,
                'height': int
            }
    
    Raises:
        ValueError: Если не удалось обработать файл
    """
    # Создаем временную директорию для нормализованных изображений
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp' / 'normalized'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    import sys
    print(f"🔵 normalize_pages_batch вызван с {len(files)} файлами", file=sys.stderr)
    sys.stderr.flush()
    
    for file in files:
        try:
            # Генерируем уникальный ID для файла
            file_id = str(uuid.uuid4())
            original_filename = file.name
            
            # Определяем расширение из оригинального имени файла
            original_ext = Path(original_filename).suffix.lower()
            if not original_ext or original_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                original_ext = '.jpg'  # По умолчанию jpg
            
            # Сохраняем исходный файл во временную директорию с оригинальным расширением
            temp_input_path = temp_dir / f'temp_{file_id}_input{original_ext}'
            import sys
            print(f"📁 Сохранение файла: {original_filename} -> {temp_input_path}", file=sys.stderr)
            sys.stderr.flush()
            with open(temp_input_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # Проверяем, что файл действительно сохранился
            if not temp_input_path.exists():
                raise ValueError(f"Файл не был сохранен: {temp_input_path}")
            
            file_size = temp_input_path.stat().st_size
            import sys
            print(f"📊 Размер сохраненного файла: {file_size} байт", file=sys.stderr)
            sys.stderr.flush()
            
            if file_size == 0:
                raise ValueError(f"Файл пуст: {temp_input_path}")
            
            # Проверяем, что файл можно прочитать как изображение
            test_image = cv2.imread(str(temp_input_path))
            if test_image is None:
                raise ValueError(f"Не удалось загрузить изображение через OpenCV: {temp_input_path}. Возможно, файл поврежден или формат не поддерживается.")
            print(f"✓ Изображение успешно загружено через OpenCV: {test_image.shape}", file=sys.stderr)
            sys.stderr.flush()
            
            # Путь для нормализованного изображения (всегда jpg для результата)
            normalized_filename = f'normalized_{file_id}.jpg'
            normalized_path = temp_dir / normalized_filename
            
            # Обрабатываем документ
            width, height = process_document(temp_input_path, normalized_path)
            
            # Удаляем временный исходный файл
            if temp_input_path.exists():
                temp_input_path.unlink()
            
            # Формируем URL для доступа к нормализованному изображению
            normalized_url = f"{settings.MEDIA_URL}temp/normalized/{normalized_filename}"
            
            results.append({
                'id': file_id,
                'original_filename': original_filename,
                'normalized_url': normalized_url,
                'width': width,
                'height': height
            })
            
        except Exception as e:
            # Если обработка не удалась, пропускаем файл и продолжаем
            import traceback
            import sys
            error_trace = traceback.format_exc()
            print(f"⚠️ Ошибка обработки файла {file.name}: {e}", file=sys.stderr)
            print(f"⚠️ Traceback:\n{error_trace}", file=sys.stderr)
            sys.stderr.flush()
            # Можно добавить информацию об ошибке в результат
            results.append({
                'id': str(uuid.uuid4()),
                'original_filename': file.name,
                'error': str(e),
                'normalized_url': None,
                'width': None,
                'height': None
            })
    
    return results

