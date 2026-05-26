from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pymongo import MongoClient

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录后再访问此页面。'

mongo_client = MongoClient
mongo_db = None


def get_mongo():
    return mongo_db
