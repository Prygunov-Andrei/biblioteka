"""
Сервис обработки документов
"""
import cv2
import numpy as np
from pathlib import Path
from dynamsoft_capture_vision_bundle import CaptureVisionRouter, LicenseManager


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


def process_document(input_path, output_path):
    """
    Обработка документа - нормализация перспективы
    
    Args:
        input_path: Путь к входному изображению (Path или str)
        output_path: Путь для сохранения обработанного изображения (Path или str)
    
    Returns:
        tuple: (width, height) размер обработанного изображения
    
    Raises:
        ValueError: Если не удалось загрузить изображение или найти документ
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    print(f"🔥 Обработка документа")
    print(f"📥 Input:  {input_path}")
    print(f"📤 Output: {output_path}")
    
    # Загружаем изображение
    image = cv2.imread(str(input_path))
    if image is None:
        raise ValueError(f"Не удалось загрузить изображение: {input_path}")
    
    orig_h, orig_w = image.shape[:2]
    print(f"📐 Исходный размер: {orig_w}x{orig_h}")
    
    # Инициализация SDK
    license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
    error_code, error_msg = LicenseManager.init_license(license_key)
    if error_code != 0:
        print(f"⚠ Ошибка лицензии: {error_msg}")
    
    # Обнаружение границ документа
    router = CaptureVisionRouter()
    result = router.capture(str(input_path), "DetectDocumentBoundaries_Default")
    
    if result is None or result.get_items() is None or len(result.get_items()) == 0:
        raise ValueError("Документ не найден на изображении")
    
    items = result.get_items()
    print(f"✓ Найдено {len(items)} документ(ов)")
    
    # Берем первый найденный документ
    quad = items[0]
    location = quad.get_location()
    points = location.points
    
    print(f"📍 Координаты углов:")
    for i, point in enumerate(points):
        print(f"  Угол {i+1}: ({point.x}, {point.y})")
    
    # Применяем перспективное преобразование
    pts = np.float32([[p.x, p.y] for p in points])
    normalized = four_point_transform(image, pts)
    
    new_h, new_w = normalized.shape[:2]
    print(f"✅ Финальный размер: {new_w}x{new_h}")
    
    # Сохраняем результат
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), normalized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"💾 Сохранено: {output_path}")
    print("🎉 Обработка завершена!")
    
    return (new_w, new_h)

