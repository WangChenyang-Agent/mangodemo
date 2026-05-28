from bson import ObjectId
from extensions import get_mongo


class BookService:
    @staticmethod
    def get_collection():
        """
        获取 MongoDB books 集合（表）
        :return: 返回 books 集合对象，用于执行数据库操作
        """
        return get_mongo()['books']

    @classmethod
    def get_books(cls, page=1, per_page=20, search=None):
        """
        分页 + 模糊查询图书列表
        :param page: 当前页码，默认第1页
        :param per_page: 每页显示条数，默认20条
        :param search: 搜索关键词，按图书名称模糊查询（不区分大小写）
        :return: 图书列表、总条数、总页数、当前页码
        """
        collection = cls.get_collection()
        query = {}
        if search:
            query['name'] = {'$regex': search, '$options': 'i'}

        total = collection.count_documents(query)
        skip = (page - 1) * per_page
        cursor = collection.find(query).skip(skip).limit(per_page)
        books = list(cursor)

        for book in books:
            book['_id'] = str(book['_id'])

        total_pages = (total + per_page - 1) // per_page
        return books, total, total_pages, page

    @classmethod
    def get_book_by_id(cls, book_id):
        """
        根据图书ID查询单本图书详情
        :param book_id: 图书的MongoDB _id（字符串格式）
        :return: 存在则返回图书字典（_id转字符串），不存在返回None
        """
        collection = cls.get_collection()
        book = collection.find_one({'_id': ObjectId(book_id)})
        if book:
            book['_id'] = str(book['_id'])
        return book

    @classmethod
    def add_book(cls, data):
        """
        新增一本图书到数据库
        :param data: 前端传入的图书信息字典
        :return: 新增成功后返回生成的图书ID（字符串格式）
        """
        collection = cls.get_collection()
        book = {
            'name': data.get('name', '').strip(),
            'price': data.get('price', '').strip(),
            'src': data.get('src', '').strip(),
            'description': data.get('description', '').strip(),
            'category': data.get('category', '').strip(),
            'stock': int(data.get('stock', 100)),
        }
        result = collection.insert_one(book)
        return str(result.inserted_id)

    @classmethod
    def update_book(cls, book_id, data):
        """
        根据ID更新图书信息
        :param book_id: 要更新的图书ID
        :param data: 要更新的图书字段字典
        :return: 无返回值，直接执行更新
        """
        collection = cls.get_collection()
        update_data = {
            'name': data.get('name', '').strip(),
            'price': data.get('price', '').strip(),
            'src': data.get('src', '').strip(),
            'description': data.get('description', '').strip(),
            'category': data.get('category', '').strip(),
            'stock': int(data.get('stock', 100)),
        }
        collection.update_one({'_id': ObjectId(book_id)}, {'$set': update_data})

    @classmethod
    def delete_book(cls, book_id):
        """
        根据ID删除一本图书
        :param book_id: 要删除的图书ID
        :return: 无返回值，直接执行删除
        """
        collection = cls.get_collection()
        collection.delete_one({'_id': ObjectId(book_id)})

    @classmethod
    def decrease_stock(cls, book_id, quantity):
        """
        扣减图书库存（下单时使用）
        :param book_id: 图书ID
        :param quantity: 要扣减的数量
        :return: 无返回值，直接执行库存自减
        """
        collection = cls.get_collection()
        collection.update_one(
            {'_id': ObjectId(book_id)},
            {'$inc': {'stock': -quantity}}
        )

    @classmethod
    def get_total_count(cls):
        """
        获取图书总数量（统计用）
        :return: 返回图书总条数
        """
        return cls.get_collection().count_documents({})