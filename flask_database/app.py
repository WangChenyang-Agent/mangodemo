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

# 应用工厂函数：创建并配置 Flask 实例
def create_app(config_class=Config):
    # 初始化 Flask 应用
    app = Flask(__name__)
    # 从配置类加载所有配置
    app.config.from_object(config_class)

    # 初始化 MySQL 数据库
    db.init_app(app)

    # 初始化登录管理模块
    login_manager.init_app(app)

    # 初始化 MongoDB 连接
    mongo = mongo_client(app.config['MONGO_URI'])
    # 获取指定的 MongoDB 数据库
    mongo_db = mongo[app.config['MONGO_DB']]

    # 将 MongoDB 数据库对象挂载到扩展模块，方便全局使用
    import extensions
    extensions.mongo_db = mongo_db

    # 注册用户加载函数：根据用户 ID 获取用户对象
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 全局请求拦截：管理员只能访问后台页面，禁止访问普通用户页面
    from flask import request, redirect, url_for
    from flask_login import current_user

    @app.before_request
    def restrict_admin_to_backend():
        # 判断：已登录 + 是管理员
        if current_user.is_authenticated and current_user.is_admin:
            # 如果访问的不是后台、不是静态文件、也不是登录/注册/登出页面
            if not request.path.startswith('/admin') and not request.path.startswith('/static') \
               and request.endpoint not in ('auth.login', 'auth.logout', 'auth.register'):
                # 强制跳转到管理员控制台
                return redirect(url_for('admin.dashboard'))

    # 导入各个路由蓝图
    from routes.auth import auth       # 登录注册相关
    from routes.books import books     # 图书展示相关
    from routes.cart import cart       # 购物车相关
    from routes.profile import profile # 用户个人中心相关
    from routes.admin import admin     # 管理员后台相关

    # 注册蓝图到应用
    app.register_blueprint(auth)
    app.register_blueprint(books)
    app.register_blueprint(cart)
    app.register_blueprint(profile)
    app.register_blueprint(admin)

    # 在应用上下文中创建数据库表并初始化数据
    with app.app_context():
        # 创建所有 MySQL 数据表（不存在则创建）
        db.create_all()
        # 执行迁移：给用户表添加余额字段（兼容旧库）
        _migrate_add_balance()
        # 创建或重置默认管理员账号
        _create_default_admin()

    return app


def _migrate_add_balance():
    """
    数据库迁移函数：
    如果 users 表不存在 balance 字段，则自动添加，用于兼容旧版本数据库
    """
    from sqlalchemy import text
    with db.engine.connect() as conn:
        # 查询 users 表是否存在 balance 字段
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'balance'"
        ))
        # 不存在则添加 balance 字段，默认 0.00
        if result.fetchone()[0] == 0:
            conn.execute(text("ALTER TABLE users ADD COLUMN balance DECIMAL(10,2) DEFAULT 0.00"))
            conn.commit()
            print('[INFO] balance 字段已添加')


def _create_default_admin():
    """
    创建默认管理员账号：
    1. 如果已存在 admin 账号 → 重置密码并设为管理员
    2. 如果不存在 → 创建新管理员账号
    """
    from models.user import User

    admin = User.query.filter_by(username='admin').first()
    if admin:
        # 已有管理员：更新密码和权限
        admin.set_password('123456')
        admin.is_admin = True
        db.session.commit()
        print('[INFO] 管理员密码已重置: admin / 123456')
    else:
        # 无管理员：创建新管理员
        admin = User(
            username='admin',
            email='admin@bookshop.com',
            is_admin=True,
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print('[INFO] 默认管理员已创建: admin / 123456')


# 创建应用实例
app = create_app()


# 主程序入口：启动 Flask
if __name__ == '__main__':
    app.run(debug=True)