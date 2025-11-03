import { useState } from 'react';
import './Sidebar.css';

const Sidebar = ({ categories, hashtags, selectedCategory, selectedHashtag, onCategorySelect, onHashtagSelect, totalBooksCount }) => {
  // Состояние для отслеживания раскрытых родительских категорий
  const [expandedCategories, setExpandedCategories] = useState(new Set());

  const toggleCategory = (categoryId) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const isCategorySelected = (category) => {
    if (!selectedCategory) return false;
    // Проверяем, выбрана ли сама категория или одна из её подкатегорий
    if (category.id === selectedCategory.id) return true;
    if (category.subcategories) {
      return category.subcategories.some(sub => sub.id === selectedCategory.id);
    }
    return false;
  };

  const isSubcategorySelected = (subcategory) => {
    return selectedCategory?.id === subcategory.id;
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        <div className="categories-section">
          <h3 className="section-title">Категории</h3>
          <ul className="categories-list">
            <li
              className={`category-item ${!selectedCategory ? 'active' : ''}`}
              onClick={() => onCategorySelect(null)}
            >
              <span className="category-name">Все категории</span>
              {totalBooksCount !== undefined && (
                <span className="category-count">({totalBooksCount})</span>
              )}
            </li>
            {categories.map((category) => {
              const hasSubcategories = category.subcategories && category.subcategories.length > 0;
              const isExpanded = expandedCategories.has(category.id);
              const isSelected = isCategorySelected(category);
              
              return (
                <li key={category.id} className="category-group">
                  <div
                    className={`category-item category-parent ${
                      isSelected ? 'active' : ''
                    } ${hasSubcategories ? 'has-children' : ''}`}
                    onClick={() => {
                      if (hasSubcategories) {
                        toggleCategory(category.id);
                      } else {
                        onCategorySelect(category);
                      }
                    }}
                  >
                    <div className="category-content">
                      {hasSubcategories && (
                        <span className="category-expand-icon">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      )}
                      <span className="category-name">{category.name}</span>
                    </div>
                    {category.books_count !== undefined && (
                      <span className="category-count">({category.books_count})</span>
                    )}
                  </div>
                  {hasSubcategories && isExpanded && (
                    <ul className="subcategories-list">
                      {category.subcategories.map((subcategory) => (
                        <li
                          key={subcategory.id}
                          className={`subcategory-item ${
                            isSubcategorySelected(subcategory) ? 'active' : ''
                          }`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onCategorySelect(subcategory);
                          }}
                        >
                          <span className="subcategory-name">{subcategory.name}</span>
                          {subcategory.books_count !== undefined && (
                            <span className="subcategory-count">({subcategory.books_count})</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
        <div className="hashtags-section">
          <h3 className="section-title">Хэштеги</h3>
          <div className="hashtags-container">
            {hashtags.length > 0 ? (
              hashtags.map((hashtag, index) => {
                // Вычисляем размер шрифта и жирность на основе частоты
                const minFontSize = 8;
                const maxFontSize = 20;
                const minCount = hashtags[hashtags.length - 1]?.count || 1;
                const maxCount = hashtags[0]?.count || 1;
                
                // Нормализуем count в диапазон 0-1
                const normalized = maxCount > minCount 
                  ? (hashtag.count - minCount) / (maxCount - minCount)
                  : 0;
                
                // Вычисляем размер шрифта (от 8px до 20px)
                const fontSize = minFontSize + (maxFontSize - minFontSize) * normalized;
                
                // Вычисляем жирность (от 300 до 700)
                const fontWeight = Math.round(300 + 400 * normalized);
                
                const isSelected = selectedHashtag?.id === hashtag.id;
                
                return (
                  <span key={hashtag.id}>
                    <span
                      className={`hashtag-link ${isSelected ? 'active' : ''}`}
                      style={{
                        fontSize: `${fontSize}px`,
                        fontWeight: fontWeight,
                      }}
                      onClick={() => onHashtagSelect(isSelected ? null : hashtag)}
                      title={`${hashtag.name} (${hashtag.count})`}
                    >
                      {hashtag.name}
                    </span>
                    {index < hashtags.length - 1 && <span className="hashtag-separator">, </span>}
                  </span>
                );
              })
            ) : (
              <span className="hashtag-item-empty">Пока нет хэштегов</span>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

