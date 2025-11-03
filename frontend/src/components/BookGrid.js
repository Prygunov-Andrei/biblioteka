import BookCard from './BookCard';
import './BookGrid.css';

const BookGrid = ({ books, loading, onAddBook }) => {
  if (loading) {
    return (
      <div className="book-grid-loading">
        <div className="loading-spinner">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="book-grid">
      {books.map((book) => (
        <BookCard key={book.id} book={book} />
      ))}
      <div className="add-book-card" onClick={onAddBook}>
        <div className="add-book-icon">+</div>
        <div className="add-book-text">ДОБАВИТЬ НОВУЮ КНИГУ</div>
      </div>
    </div>
  );
};

export default BookGrid;

