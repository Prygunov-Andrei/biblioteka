import './Sidebar.css';

const Sidebar = ({ categories, hashtags, selectedCategory, onCategorySelect }) => {
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
              Все категории
            </li>
            {categories.map((category) => (
              <li
                key={category.id}
                className={`category-item ${
                  selectedCategory?.id === category.id ? 'active' : ''
                }`}
                onClick={() => onCategorySelect(category)}
              >
                {category.name}
              </li>
            ))}
          </ul>
        </div>
        <div className="hashtags-section">
          <h3 className="section-title">Хэштеги</h3>
          <ul className="hashtags-list">
            {hashtags.length > 0 ? (
              hashtags.map((hashtag) => (
                <li key={hashtag.id} className="hashtag-item">
                  {hashtag.name}
                </li>
              ))
            ) : (
              <li className="hashtag-item-empty">Пока нет хэштегов</li>
            )}
          </ul>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

