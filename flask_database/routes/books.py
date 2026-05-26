from flask import Blueprint, render_template, request, current_app
from services.book_service import BookService

books = Blueprint('books', __name__)


@books.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    per_page = current_app.config.get('BOOKS_PER_PAGE', 20)

    book_list, total, total_pages, current_page = BookService.get_books(
        page=page, per_page=per_page, search=search or None
    )

    return render_template(
        'index.html',
        books=book_list,
        total=total,
        total_pages=total_pages,
        current_page=current_page,
        search=search,
    )


@books.route('/book/<book_id>')
def book_detail(book_id):
    book = BookService.get_book_by_id(book_id)
    if not book:
        return render_template('book_detail.html', book=None), 404
    return render_template('book_detail.html', book=book)
