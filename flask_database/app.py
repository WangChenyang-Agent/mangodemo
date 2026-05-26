from flask import Flask
from config import Config
from extensions import db, login_manager, mongo_client

"""
普通用户
账号：root
密码：123456

管理用户
账号：admin
密码：123456
"""

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize MySQL
    db.init_app(app)

    # Initialize Flask-Login
    login_manager.init_app(app)

    # Initialize MongoDB
    mongo = mongo_client(app.config['MONGO_URI'])
    mongo_db = mongo[app.config['MONGO_DB']]

    # Make mongo_db accessible in the extensions module
    import extensions
    extensions.mongo_db = mongo_db

    # Register user loader
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Redirect admin users away from regular pages
    from flask import request, redirect, url_for
    from flask_login import current_user

    @app.before_request
    def restrict_admin_to_backend():
        if current_user.is_authenticated and current_user.is_admin:
            if not request.path.startswith('/admin') and not request.path.startswith('/static') \
               and request.endpoint not in ('auth.login', 'auth.logout', 'auth.register'):
                return redirect(url_for('admin.dashboard'))

    # Register blueprints
    from routes.auth import auth
    from routes.books import books
    from routes.cart import cart
    from routes.profile import profile
    from routes.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(books)
    app.register_blueprint(cart)
    app.register_blueprint(profile)
    app.register_blueprint(admin)

    # Create tables and default admin
    with app.app_context():
        db.create_all()
        _migrate_add_balance()
        _create_default_admin()

    return app


def _migrate_add_balance():
    """Add balance column if not exists (for existing databases)."""
    from sqlalchemy import text
    with db.engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'balance'"
        ))
        if result.fetchone()[0] == 0:
            conn.execute(text("ALTER TABLE users ADD COLUMN balance DECIMAL(10,2) DEFAULT 0.00"))
            conn.commit()
            print('[INFO] balance 字段已添加')


def _create_default_admin():
    """Create or update default admin user."""
    from models.user import User

    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('123456')
        admin.is_admin = True
        db.session.commit()
        print('[INFO] 管理员密码已重置: admin / 123456')
    else:
        admin = User(
            username='admin',
            email='admin@bookshop.com',
            is_admin=True,
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print('[INFO] 默认管理员已创建: admin / 123456')


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
