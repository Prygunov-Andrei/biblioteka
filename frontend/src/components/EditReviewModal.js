import { useState, useEffect } from 'react';
import './EditReviewModal.css';
import StarRating from './StarRating';

const EditReviewModal = ({ isOpen, review, bookId, onSave, onCancel }) => {
  const [rating, setRating] = useState(null);
  const [reviewText, setReviewText] = useState('');
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (review) {
      setRating(review.rating !== null && review.rating !== undefined ? review.rating : null);
      setReviewText(review.review_text || '');
    } else {
      // Новый отзыв
      setRating(null);
      setReviewText('');
    }
    setErrors({});
  }, [review, isOpen]);

  const handleStarClick = (starValue) => {
    setRating(rating === starValue ? null : starValue);
    setErrors(prev => ({ ...prev, rating: null }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Валидация: хотя бы одно поле должно быть заполнено
    if (rating === null && !reviewText.trim()) {
      setErrors({ general: 'Заполните хотя бы одно поле: звезды или текст отзыва' });
      return;
    }

    const reviewData = {};
    if (rating !== null) {
      reviewData.rating = rating;
    }
    if (reviewText.trim()) {
      reviewData.review_text = reviewText.trim();
    }

    onSave(reviewData);
  };

  const handleCancel = () => {
    setRating(null);
    setReviewText('');
    setErrors({});
    onCancel();
  };

  if (!isOpen) return null;

  return (
    <div className="edit-review-modal-overlay" onClick={handleCancel}>
      <div className="edit-review-modal" onClick={(e) => e.stopPropagation()}>
        <div className="edit-review-modal-header">
          <h2>{review ? 'Редактировать отзыв' : 'Оставить отзыв'}</h2>
          <button className="edit-review-modal-close" onClick={handleCancel}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="edit-review-modal-form">
          <div className="edit-review-modal-field">
            <label className="edit-review-modal-label">Оценка (1-5 звезд):</label>
            <div className="edit-review-modal-stars">
              {[1, 2, 3, 4, 5].map((starValue) => (
                <button
                  key={starValue}
                  type="button"
                  className={`edit-review-modal-star ${rating >= starValue ? 'star-selected' : ''}`}
                  onClick={() => handleStarClick(starValue)}
                  title={`${starValue} ${starValue === 1 ? 'звезда' : starValue < 5 ? 'звезды' : 'звезд'}`}
                >
                  ★
                </button>
              ))}
            </div>
            {rating !== null && (
              <div className="edit-review-modal-rating-preview">
                <StarRating rating={rating} size="small" />
              </div>
            )}
          </div>

          <div className="edit-review-modal-field">
            <label className="edit-review-modal-label" htmlFor="review-text">
              Текст отзыва:
            </label>
            <textarea
              id="review-text"
              className="edit-review-modal-textarea"
              value={reviewText}
              onChange={(e) => {
                setReviewText(e.target.value);
                setErrors(prev => ({ ...prev, review_text: null }));
              }}
              placeholder="Напишите ваш отзыв о книге..."
              rows={6}
            />
          </div>

          {errors.general && (
            <div className="edit-review-modal-error">{errors.general}</div>
          )}

          <div className="edit-review-modal-footer">
            <button type="button" className="edit-review-modal-button edit-review-modal-button-cancel" onClick={handleCancel}>
              Отмена
            </button>
            <button type="submit" className="edit-review-modal-button edit-review-modal-button-save">
              {review ? 'Сохранить изменения' : 'Оставить отзыв'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditReviewModal;

