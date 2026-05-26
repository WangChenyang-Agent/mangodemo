from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db, get_mongo
from services.book_service import BookService
from services.cart_service import CartService

cart = Blueprint('cart', __name__)


def _parse_price(price_str):
    """Parse price string like '¥39.00' to float."""
    if not price_str:
        return 0.0
    return float(price_str.replace('¥', '').replace(',', '').strip())


@cart.route('/cart')
@login_required
def view():
    user_cart = CartService.get_cart(current_user.id)
    return render_template('cart.html', cart=user_cart)


@cart.route('/cart/add/<book_id>', methods=['POST'])
@login_required
def add(book_id):
    book = BookService.get_book_by_id(book_id)
    if not book:
        flash('图书不存在。', 'danger')
        return redirect(url_for('books.index'))

    stock = book.get('stock', 0)
    if stock <= 0:
        flash('该图书已售罄。', 'warning')
        return redirect(request.referrer or url_for('books.index'))

    CartService.add_item(current_user.id, book)
    flash(f'《{book["name"]}》已加入购物车。', 'success')
    return redirect(request.referrer or url_for('books.index'))


@cart.route('/cart/remove/<book_id>', methods=['POST'])
@login_required
def remove(book_id):
    CartService.remove_item(current_user.id, book_id)
    flash('已从购物车移除。', 'info')
    return redirect(url_for('cart.view'))


@cart.route('/cart/update/<book_id>', methods=['POST'])
@login_required
def update(book_id):
    quantity = request.form.get('quantity', 1, type=int)
    CartService.update_quantity(current_user.id, book_id, quantity)
    return redirect(url_for('cart.view'))


@cart.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user_cart = CartService.get_cart(current_user.id)
    items = user_cart.get('cart_items', [])
    if not items:
        flash('购物车为空，请先添加商品。', 'warning')
        return redirect(url_for('books.index'))

    # Check stock for all items
    for item in items:
        book = BookService.get_book_by_id(item.get('book_id'))
        if not book:
            flash(f'《{item.get("name")}》已下架，请从购物车移除。', 'danger')
            return redirect(url_for('cart.view'))
        current_stock = book.get('stock', 0)
        if current_stock < item.get('quantity', 1):
            flash(f'《{item.get("name")}》库存不足（剩余 {current_stock} 本），请调整数量。', 'danger')
            return redirect(url_for('cart.view'))

    # Calculate total price
    total = sum(_parse_price(item.get('price', '')) * item.get('quantity', 1) for item in items)

    # Check balance
    balance = float(current_user.balance or 0)
    if balance < total:
        flash(f'余额不足！需要 ¥{total:.2f}，当前余额 ¥{balance:.2f}，请先充值。', 'danger')
        return redirect(url_for('profile.view'))

    # Deduct balance
    balance_after = balance - total
    current_user.balance = balance_after
    db.session.commit()

    # Record transaction
    get_mongo()['transactions'].insert_one({
        'user_id': current_user.id,
        'type': 'purchase',
        'amount': -total,
        'balance_after': balance_after,
        'cart_items': items,
        'created_at': datetime.utcnow(),
    })

    # Decrease stock for each book
    for item in items:
        BookService.decrease_stock(item.get('book_id'), item.get('quantity', 1))

    CartService.clear_cart(current_user.id)
    flash(f'下单成功！共消费 ¥{total:.2f}，余额剩余 ¥{balance_after:.2f}。', 'success')
    return redirect(url_for('books.index'))
