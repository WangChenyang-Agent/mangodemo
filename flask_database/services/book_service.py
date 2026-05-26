from bson import ObjectId
from extensions import get_mongo


class BookService:
    @staticmethod
    def get_collection():
        return get_mongo()['books']

    @classmethod
    def get_books(cls, page=1, per_page=20, search=None):
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
        collection = cls.get_collection()
        book = collection.find_one({'_id': ObjectId(book_id)})
        if book:
            book['_id'] = str(book['_id'])
        return book

    @classmethod
    def add_book(cls, data):
        collection = cls.get_collection()
        book = {
            'name': data.get('name', '').strip(),
            'price': data.get('price', '').strip(),
            'src': data.get('src', '').strip(),
            'description': data.get('description', '').strip(),
            'category': data.get('category', '').strip(),
            'stock': int(data.get('stock', 0)),
        }
        result = collection.insert_one(book)
        return str(result.inserted_id)

    @classmethod
    def update_book(cls, book_id, data):
        collection = cls.get_collection()
        update_data = {
            'name': data.get('name', '').strip(),
            'price': data.get('price', '').strip(),
            'src': data.get('src', '').strip(),
            'description': data.get('description', '').strip(),
            'category': data.get('category', '').strip(),
            'stock': int(data.get('stock', 0)),
        }
        collection.update_one({'_id': ObjectId(book_id)}, {'$set': update_data})

    @classmethod
    def delete_book(cls, book_id):
        collection = cls.get_collection()
        collection.delete_one({'_id': ObjectId(book_id)})

    @classmethod
    def decrease_stock(cls, book_id, quantity):
        collection = cls.get_collection()
        collection.update_one(
            {'_id': ObjectId(book_id)},
            {'$inc': {'stock': -quantity}}
        )

    @classmethod
    def get_total_count(cls):
        return cls.get_collection().count_documents({})
