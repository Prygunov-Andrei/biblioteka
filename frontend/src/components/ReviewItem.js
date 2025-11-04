import './ReviewItem.css';
import StarRating from './StarRating';

const ReviewItem = ({ review, currentUserId, onEdit, onDelete }) => {
  // Проверяем, является ли отзыв собственным
  // review.user может быть числом (ID) или объектом с полем id
  const reviewUserId = typeof review.user === 'object' && review.user !== null 
    ? review.user.id 
    : review.user;
  const isOwnReview = currentUserId && reviewUserId && reviewUserId === currentUserId;
  
  const handleEdit = (e) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit(review);
    }
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(review.id);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="review-item">
      <div className="review-item-header">
        <div className="review-item-user">
          <span className="review-item-username">{review.user_username || (review.user && typeof review.user === 'object' ? review.user.username : 'Пользователь')}</span>
          <span className="review-item-date">{formatDate(review.created_at)}</span>
        </div>
        {isOwnReview && (
          <div className="review-item-actions">
            <button 
              className="review-item-action review-item-action-edit" 
              onClick={handleEdit}
              title="Редактировать отзыв"
            >
              ✏️
            </button>
            <button 
              className="review-item-action review-item-action-delete" 
              onClick={handleDelete}
              title="Удалить отзыв"
            >
              🗑️
            </button>
          </div>
        )}
      </div>
      {review.rating !== null && review.rating !== undefined && (
        <div className="review-item-rating">
          <StarRating rating={review.rating} size="small" />
        </div>
      )}
      {review.review_text && (
        <div className="review-item-text">
          {review.review_text}
        </div>
      )}
    </div>
  );
};

export default ReviewItem;

