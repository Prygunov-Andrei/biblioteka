import './Filters.css';

const Filters = ({ filters, onFilterChange, stats }) => {
  const filterButtons = [
    { 
      key: 'status', 
      value: 'none', 
      label: 'НЕ ПРОЧИТАНО',
      count: stats?.status?.none || 0
    },
    { 
      key: 'status', 
      value: 'reading', 
      label: 'ЧИТАЮ',
      count: stats?.status?.reading || 0
    },
    { 
      key: 'status', 
      value: 'read', 
      label: 'ПРОЧИТАНО',
      count: stats?.status?.read || 0
    },
    { 
      key: 'status', 
      value: 'want_to_read', 
      label: 'БУДУ ЧИТАТЬ',
      count: stats?.status?.want_to_read || 0
    },
    { 
      key: 'status', 
      value: 'want_to_reread', 
      label: 'БУДУ ПЕРЕЧИТЫВАТЬ',
      count: stats?.status?.want_to_reread || 0
    },
    { 
      key: 'has_reviews', 
      label: 'С ОТЗЫВАМИ',
      count: stats?.with_reviews || 0
    },
    { 
      key: 'has_electronic', 
      label: 'ЕСТЬ ЭЛЕКТРОННАЯ ВЕРСИЯ',
      count: stats?.with_electronic || 0
    },
    { 
      key: 'recently_added', 
      label: 'ДОБАВЛЕНА НЕДАВНО',
      count: stats?.recently_added || 0
    },
  ];

  const handleFilterClick = (filterKey, filterValue) => {
    if (filterKey === 'status') {
      // Если статус уже выбран, снимаем фильтр
      const newValue = filters.status === filterValue ? null : filterValue;
      onFilterChange(filterKey, newValue);
    } else {
      // Для булевых фильтров просто переключаем
      onFilterChange(filterKey, !filters[filterKey]);
    }
  };

  const isFilterActive = (filterKey, filterValue) => {
    if (filterKey === 'status') {
      return filters.status === filterValue;
    }
    return filters[filterKey] === true;
  };

  return (
    <div className="filters">
      {filterButtons.map((filter, index) => {
        const active = isFilterActive(filter.key, filter.value);
        return (
          <button
            key={index}
            className={`filter-button ${active ? 'active' : ''}`}
            onClick={() => handleFilterClick(filter.key, filter.value)}
          >
            {filter.label}
            {filter.count !== undefined && (
              <span className="filter-count"> - {filter.count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default Filters;

