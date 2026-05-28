# 图书商城

基于 Flask + Scrapy 构建的图书商城系统，支持用户注册登录、图书浏览购买、购物车管理、充值结算，以及管理员后台管理和AI销售分析。

## 项目结构

```
mangodemo/
├── flask_database/          # Flask Web 应用
│   ├── models/             # 数据库模型（MySQL）
│   ├── routes/             # 路由控制器
│   ├── services/           # 业务逻辑层
│   ├── static/             # 静态资源
│   ├── templates/          # HTML 模板
│   ├── app.py              # 应用入口
│   ├── config.py           # 配置文件
│   ├── extensions.py       # 扩展初始化
│   ├── requirements.txt    # Python 依赖
│   └── .env                # 环境变量（需自行创建）
└── scrapy_dangdang_38/     # Scrapy 爬虫项目
    ├── scrapy_dangdang_38/
    │   ├── spiders/        # 爬虫文件
    │   ├── items.py        # 数据项定义
    │   ├── pipelines.py    # 数据处理管道
    │   └── settings.py     # 爬虫配置
    └── scrapy.cfg          # Scrapy 配置
```

## 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 框架 | Flask | >=3.0 |
| ORM | Flask-SQLAlchemy | >=3.1 |
| 认证 | Flask-Login | >=0.6 |
| MySQL驱动 | PyMySQL | >=1.1 |
| MongoDB驱动 | PyMongo | >=4.6 |
| 环境变量 | python-dotenv | >=1.0 |
| 爬虫 | Scrapy | >=2.0 |

## 功能特性

### 用户功能
- 用户注册与登录
- 图书浏览与搜索
- 购物车管理（添加/删除/修改数量）
- 余额充值
- 订单结算
- 交易记录查询

### 管理员功能
- 仪表盘（数据统计、销售图表）
- 图书管理（增删改查、批量设置库存）
- 用户管理（增删改查、权限设置）
- 交易记录查看
- AI销售分析报告

## 数据库设计

### MySQL（用户数据）
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    balance DECIMAL(10,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### MongoDB（业务数据）
- **books**: 图书信息（名称、价格、图片、描述、分类、库存）
- **carts**: 购物车（用户ID、商品列表）
- **transactions**: 交易记录（充值、购买）

## 快速开始

### 环境要求
- Python 3.10+
- MySQL 5.7+ / MariaDB 10.2+
- MongoDB 4.0+

### 安装依赖

```bash
# 进入 Flask 应用目录
cd flask_database

# 安装依赖
pip install -r requirements.txt
```

### 配置数据库

1. 创建 MySQL 数据库：
```sql
CREATE DATABASE flask_db CHARACTER SET utf8mb4;
```

2. 创建 `.env` 文件配置环境变量：
```env
# Flask 配置
SECRET_KEY=dev-secret-key-change-in-production

# MySQL 配置
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=flask_db

# MongoDB 配置
MONGO_URI=mongodb://localhost:27017
MONGO_DB=dangdang

# DeepSeek API 配置（用于 AI 分析）
DEEPSEEK_API_KEY=your-api-key-here
```

> **注意**：`.env` 文件包含敏感信息，已添加到 `.gitignore`，请不要提交到版本库。

### 运行应用

```bash
python app.py
```

访问 http://localhost:5000 即可进入商城首页。

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 普通用户 | root | 123456 |
| 管理员 | admin | 123456 |

## 爬虫使用

### 运行爬虫

```bash
cd scrapy_dangdang_38
scrapy crawl dang
```

爬虫会自动爬取当当网图书数据并保存到 MongoDB。

## API 接口

### 用户认证
- `GET /login` - 登录页面
- `POST /login` - 登录提交
- `GET /register` - 注册页面
- `POST /register` - 注册提交
- `GET /logout` - 退出登录

### 图书管理
- `GET /` - 图书列表（支持搜索）
- `GET /book/<book_id>` - 图书详情

### 购物车
- `GET /cart` - 查看购物车
- `POST /cart/add/<book_id>` - 添加商品
- `POST /cart/remove/<book_id>` - 删除商品
- `POST /cart/update/<book_id>` - 更新数量
- `POST /cart/checkout` - 结算订单

### 用户中心
- `GET /profile` - 用户资料与交易记录
- `POST /profile/recharge` - 充值

### 管理员接口
- `GET /admin/` - 仪表盘
- `GET /admin/books` - 图书管理
- `GET /admin/users` - 用户管理
- `GET /admin/billing` - 交易记录
- `POST /admin/api/analysis` - AI分析

## 项目亮点

1. **双数据库架构**：MySQL 存储结构化用户数据，MongoDB 存储非结构化业务数据
2. **AI 销售分析**：集成 DeepSeek API 生成专业销售报告
3. **响应式界面**：基于 Bootstrap 的现代化 UI
4. **权限控制**：管理员与普通用户分离的访问控制
5. **数据统计可视化**：分类销售图表、热门图书排行

## 开发说明

### 代码规范
- 遵循 PEP 8 编码规范
- 使用 Blueprint 模块化路由
- 服务层与路由解耦
- 使用 Flask-Login 进行身份认证

### 扩展开发
- 新功能应添加到对应模块
- 数据库操作应封装到 services 层
- 模板继承自 base.html 或 admin_base.html

## 许可证

MIT License
