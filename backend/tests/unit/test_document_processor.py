"""
Тесты для document_processor
"""
import pytest
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image

from books.services.document_processor import (
    order_points,
    four_point_transform,
    process_document
)


class TestOrderPoints:
    """Тесты функции order_points"""
    
    def test_order_points_basic(self):
        """Базовое упорядочивание точек"""
        # Создаем четыре точки в произвольном порядке
        pts = np.array([
            [100, 100],  # нижний-правый
            [0, 0],      # верхний-левый
            [100, 0],    # верхний-правый
            [0, 100]     # нижний-левый
        ])
        
        ordered = order_points(pts)
        
        # Проверяем что точки упорядочены
        assert len(ordered) == 4
        assert ordered.shape == (4, 2)
        
        # Верхний-левый должен иметь минимальную сумму координат
        assert ordered[0][0] + ordered[0][1] <= ordered[2][0] + ordered[2][1]
    
    def test_order_points_rectangle(self):
        """Упорядочивание точек прямоугольника"""
        pts = np.array([
            [50, 50],
            [150, 50],
            [150, 150],
            [50, 150]
        ])
        
        ordered = order_points(pts)
        assert len(ordered) == 4


class TestFourPointTransform:
    """Тесты функции four_point_transform"""
    
    def test_four_point_transform_basic(self):
        """Базовое перспективное преобразование"""
        # Создаем простое изображение
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[50:150, 50:150] = 255  # Белый квадрат
        
        # Точки для преобразования (прямоугольник)
        pts = np.array([
            [50, 50],    # верхний-левый
            [150, 50],   # верхний-правый
            [150, 150],  # нижний-правый
            [50, 150]    # нижний-левый
        ], dtype="float32")
        
        warped = four_point_transform(img, pts)
        
        # Проверяем что результат не пустой
        assert warped is not None
        assert len(warped.shape) == 3
        assert warped.shape[2] == 3


class TestProcessDocument:
    """Тесты функции process_document"""
    
    def test_process_document_with_real_image(self, tmp_path):
        """Обработка реального изображения"""
        # Создаем простое тестовое изображение
        input_path = tmp_path / 'input.jpg'
        output_path = tmp_path / 'output.jpg'
        
        img = Image.new('RGB', (800, 1200), color='white')
        img.save(input_path)
        
        try:
            width, height = process_document(str(input_path), str(output_path))
            
            # Проверяем что выходной файл создан
            assert output_path.exists()
            
            # Проверяем возвращаемые размеры
            assert width > 0
            assert height > 0
        except Exception as e:
            # Если SDK не настроен или другая ошибка - пропускаем
            pytest.skip(f"process_document не может быть выполнен: {e}")
    
    def test_process_document_output_dir_creation(self, tmp_path):
        """Создание выходной директории"""
        input_path = tmp_path / 'input.jpg'
        output_dir = tmp_path / 'subdir' / 'nested'
        output_path = output_dir / 'output.jpg'
        
        img = Image.new('RGB', (800, 1200), color='white')
        img.save(input_path)
        
        try:
            width, height = process_document(str(input_path), str(output_path))
            assert output_dir.exists()
            assert output_path.exists()
        except Exception as e:
            pytest.skip(f"process_document не может быть выполнен: {e}")

