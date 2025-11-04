import BookCard from './BookCard';
import './BookGrid.css';

const BookGrid = ({ books, loading }) => {
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
    </div>
  );
};

export default BookGrid;

