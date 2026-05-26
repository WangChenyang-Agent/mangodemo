from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.book_service import BookService
from models.user import User
from extensions import db, get_mongo

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('需要管理员权限。', 'danger')
            return redirect(url_for('books.index'))
        return f(*args, **kwargs)
    return decorated


def _parse_price(price_str):
    if not price_str:
        return 0.0
    return float(price_str.replace('¥', '').replace(',', '').strip())


def _get_stats():
    return {
        'book_count': BookService.get_total_count(),
        'user_count': User.query.count(),
        'total_sales': sum(
            abs(t.get('amount', 0))
            for t in get_mongo()['transactions'].find({'type': 'purchase'})
        ),
    }


def _get_chart_data():
    category_sales = {}
    for t in get_mongo()['transactions'].find({'type': 'purchase'}):
        for item in t.get('cart_items', []):
            book_id = item.get('book_id')
            if book_id:
                book = BookService.get_book_by_id(book_id)
                cat = (book.get('category') if book and book.get('category') else '未分类').strip()
            else:
                cat = '未分类'
            price = _parse_price(item.get('price', '')) * item.get('quantity', 1)
            category_sales[cat] = category_sales.get(cat, 0) + price

    categories = list(category_sales.keys())
    values = [round(v, 2) for v in category_sales.values()]

    book_sales = {}
    for t in get_mongo()['transactions'].find({'type': 'purchase'}):
        for item in t.get('cart_items', []):
            name = item.get('name', '未知')
            qty = item.get('quantity', 1)
            book_sales[name] = book_sales.get(name, 0) + qty

    top_books = sorted(book_sales.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'categories': categories,
        'values': values,
        'top_books': [{'name': n[:12], 'count': c} for n, c in top_books],
    }


# ============= Dashboard =============

@admin.route('/')
@admin_required
def dashboard():
    stats = _get_stats()
    chart = _get_chart_data()
    return render_template('admin/dashboard.html', **stats, chart=chart)


# ============= Books =============

@admin.route('/books')
@admin_required
def books():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    book_list, total, total_pages, current_page = BookService.get_books(
        page=page, per_page=20, search=search or None
    )
    return render_template(
        'admin/books.html',
        books=book_list, total=total,
        total_pages=total_pages, current_page=current_page,
        search=search,
    )


@admin.route('/book/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        BookService.add_book({
            'name': request.form.get('name', ''),
            'price': request.form.get('price', ''),
            'src': request.form.get('src', ''),
            'description': request.form.get('description', ''),
            'category': request.form.get('category', ''),
            'stock': request.form.get('stock', 100),
        })
        flash('图书添加成功。', 'success')
        return redirect(url_for('admin.books'))
    return render_template('admin/add_book.html')


@admin.route('/book/edit/<book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book = BookService.get_book_by_id(book_id)
    if not book:
        flash('图书不存在。', 'danger')
        return redirect(url_for('admin.books'))
    if request.method == 'POST':
        BookService.update_book(book_id, {
            'name': request.form.get('name', ''),
            'price': request.form.get('price', ''),
            'src': request.form.get('src', ''),
            'description': request.form.get('description', ''),
            'category': request.form.get('category', ''),
            'stock': request.form.get('stock', 0),
        })
        flash('图书更新成功。', 'success')
        return redirect(url_for('admin.books'))
    return render_template('admin/edit_book.html', book=book)


@admin.route('/book/delete/<book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    BookService.delete_book(book_id)
    flash('图书已删除。', 'info')
    return redirect(url_for('admin.books'))


@admin.route('/book/batch-stock', methods=['POST'])
@admin_required
def batch_stock():
    stock = request.form.get('stock', 100, type=int)
    get_mongo()['books'].update_many({}, {'$set': {'stock': stock}})
    flash(f'全部图书库存已更新为 {stock}。', 'success')
    return redirect(url_for('admin.books'))


# ============= Users =============

@admin.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    per_page = 20
    query = User.query
    if search:
        query = query.filter(
            db.or_(User.username.contains(search), User.email.contains(search))
        )
    total = query.count()
    user_list = query.order_by(User.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    return render_template(
        'admin/users.html',
        users=user_list, total=total,
        total_pages=total_pages, current_page=page,
        search=search,
    )


@admin.route('/user/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('请填写所有字段。', 'danger')
        elif len(password) < 6:
            flash('密码长度至少6位。', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('用户名已存在。', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('邮箱已被注册。', 'danger')
        else:
            user = User(
                username=username,
                email=email,
                is_admin=request.form.get('is_admin') == '1',
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'用户 {username} 创建成功。', 'success')
            return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html')


@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在。', 'danger')
        return redirect(url_for('admin.users'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()

        existing = User.query.filter(User.username == username, User.id != user_id).first()
        if existing:
            flash('用户名已存在。', 'danger')
        else:
            user.username = username
            user.email = email
            user.is_admin = request.form.get('is_admin') == '1'
            password = request.form.get('password', '')
            if password:
                user.set_password(password)
            db.session.commit()
            flash('用户信息已更新。', 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', u=user)


@admin.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在。', 'danger')
    elif user.id == current_user.id:
        flash('不能删除自己。', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'用户 {user.username} 已删除。', 'info')
    return redirect(url_for('admin.users'))


@admin.route('/user/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在。', 'danger')
    elif user.id == current_user.id:
        flash('不能修改自己的管理员权限。', 'danger')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'用户 {user.username} 的管理员权限已{"授予" if user.is_admin else "撤销"}。', 'success')
    return redirect(url_for('admin.users'))


# ============= Billing =============

@admin.route('/billing')
@admin_required
def billing():
    page = request.args.get('page', 1, type=int)
    per_page = 30
    collection = get_mongo()['transactions']
    total = collection.count_documents({})
    transactions = list(
        collection.find().sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
    )
    total_pages = (total + per_page - 1) // per_page
    return render_template(
        'admin/billing.html',
        transactions=transactions, total=total,
        total_pages=total_pages, current_page=page,
    )


# ============= AI Analysis =============

DEEPSEEK_API_KEY = 'sk-c2375e0f8280453eb6fbfa0ffd2aa8ad'


@admin.route('/api/analysis', methods=['POST'])
@admin_required
def ai_analysis():
    import requests

    stats = _get_stats()
    chart = _get_chart_data()

    category_lines = '\n'.join(
        f'  - {c}: ¥{v:.2f}' for c, v in zip(chart['categories'], chart['values'])
    ) if chart['categories'] else '暂无分类数据'
    top_lines = '\n'.join(
        '  - {}: {}本'.format(b['name'], b['count']) for b in chart['top_books']
    ) if chart['top_books'] else '暂无销量数据'

    purchase_count = get_mongo()['transactions'].count_documents({'type': 'purchase'})
    recharge_total = sum(
        t.get('amount', 0)
        for t in get_mongo()['transactions'].find({'type': 'recharge'})
    )

    prompt = f"""你是一个图书商城的销售数据分析师。请根据以下数据，给出专业的销售分析报告（200字以内），包括：
1. 整体销售概况
2. 热销品类和图书趋势
3. 一条具体的经营建议

数据如下：
- 图书总量：{stats['book_count']} 本
- 注册用户：{stats['user_count']} 人
- 总销售额：¥{stats['total_sales']:.2f}
- 成交订单数：{purchase_count} 笔
- 充值总额：¥{recharge_total:.2f}

各分类销售额：
{category_lines}

图书销量 TOP10：
{top_lines}"""

    try:
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的电商数据分析师。回复简洁、专业、有数据支撑。'},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0.7,
                'max_tokens': 600,
            },
            timeout=30,
        )
        resp.raise_for_status()
        analysis = resp.json()['choices'][0]['message']['content']
        return {'analysis': analysis}
    except Exception as e:
        return {'error': f'AI 分析请求失败：{str(e)}'}
