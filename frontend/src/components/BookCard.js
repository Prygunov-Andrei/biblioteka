import './BookCard.css';

const BookCard = ({ book }) => {
  // Получаем первое изображение книги
  // images может быть массивом объектов BookImageSerializer с полем image_url
  const bookImage = book.images && book.images.length > 0 
    ? book.images[0].image_url 
    : null;
  
  // Получаем авторов
  const authors = book.authors || [];
  const authorsText = authors.length > 0 
    ? authors.map(a => a.full_name || a).join(', ')
    : 'Автор не указан';

  return (
    <div className="book-card">
      <div className="book-card-image-container">
        {bookImage ? (
          <img 
            src={bookImage} 
            alt={book.title}
            className="book-card-image"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : (
          <div className="book-card-placeholder">
            <span className="book-icon">📚</span>
          </div>
        )}
      </div>
      <div className="book-card-info">
        <h3 className="book-card-title">{book.title}</h3>
        <p className="book-card-author">{authorsText}</p>
      </div>
    </div>
  );
};

export default BookCard;

