import os
from pathlib import Path

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # MySQL
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'flask_database')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MongoDB
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
    MONGO_DB = 'dangdang'

    # Pagination
    BOOKS_PER_PAGE = 20

    # DeepSeek API
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
