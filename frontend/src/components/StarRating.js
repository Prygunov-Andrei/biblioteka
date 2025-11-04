import './StarRating.css';

const StarRating = ({ rating, maxRating = 5, size = 'medium', showValue = false }) => {
  // Если rating null или undefined, не показываем звезды
  if (rating === null || rating === undefined) {
    return null;
  }

  const numericRating = typeof rating === 'number' ? rating : parseFloat(rating);
  
  if (isNaN(numericRating) || numericRating < 0) {
    return null;
  }

  const fullStars = Math.floor(numericRating);
  const hasHalfStar = numericRating % 1 >= 0.5;
  const emptyStars = maxRating - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className={`star-rating star-rating-${size}`}>
      {[...Array(fullStars)].map((_, i) => (
        <span key={`full-${i}`} className="star star-full">★</span>
      ))}
      {hasHalfStar && (
        <span className="star star-half">★</span>
      )}
      {[...Array(emptyStars)].map((_, i) => (
        <span key={`empty-${i}`} className="star star-empty">☆</span>
      ))}
      {showValue && (
        <span className="star-rating-value">({numericRating.toFixed(1)})</span>
      )}
    </div>
  );
};

export default StarRating;

