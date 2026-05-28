from extensions import get_mongo


class CartService:
    @staticmethod
    def get_collection():
        """
        获取 MongoDB carts 购物车集合（表）
        :return: 返回 carts 集合对象，用于执行数据库操作
        """
        return get_mongo()['carts']

    @classmethod
    def get_cart(cls, user_id):
        """
        根据用户ID获取完整购物车数据
        :param user_id: 用户唯一标识
        :return: 格式化后的购物车字典（_id、book_id均转为字符串），无购物车则返回空购物车
        """
        collection = cls.get_collection()
        cart = collection.find_one({'user_id': user_id})
        if cart:
            cart = cls._normalize_cart(cart)
            cart['_id'] = str(cart['_id'])
            for item in cart.get('cart_items', []):
                if 'book_id' in item:
                    item['book_id'] = str(item['book_id'])
        else:
            cart = {'user_id': user_id, 'cart_items': []}
        return cart

    @classmethod
    def _normalize_cart(cls, cart):
        """
        购物车数据格式兼容：将旧字段 items 迁移为 cart_items
        :param cart: 原始购物车数据
        :return: 格式统一后的购物车数据
        """
        if 'items' in cart and 'cart_items' not in cart:
            cart['cart_items'] = cart.pop('items')
        if 'cart_items' not in cart:
            cart['cart_items'] = []
        return cart

    @classmethod
    def add_item(cls, user_id, book):
        """
        向用户购物车添加商品（已存在则数量+1，不存在则新增）
        :param user_id: 用户ID
        :param book: 图书对象（包含_id、name、price、src等信息）
        :return: 无返回值，直接执行添加/数量+1操作
        """
        collection = cls.get_collection()
        book_id = book['_id'] if isinstance(book['_id'], str) else str(book['_id'])

        cart = collection.find_one({'user_id': user_id})
        if not cart:
            cart = {'user_id': user_id, 'cart_items': []}
            collection.insert_one(cart)
        else:
            cart = cls._normalize_cart(cart)

        for item in cart.get('cart_items', []):
            if str(item.get('book_id')) == book_id:
                item['quantity'] = item.get('quantity', 1) + 1
                collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'cart_items': cart['cart_items']}}
                )
                return

        cart['cart_items'].append({
            'book_id': book_id,
            'name': book.get('name', ''),
            'price': book.get('price', ''),
            'src': book.get('src', ''),
            'quantity': 1,
        })
        collection.update_one(
            {'user_id': user_id},
            {'$set': {'cart_items': cart['cart_items']}}
        )

    @classmethod
    def remove_item(cls, user_id, book_id):
        """
        根据用户ID和图书ID，从购物车中删除指定商品
        :param user_id: 用户ID
        :param book_id: 要删除的图书ID
        :return: 无返回值，直接执行删除
        """
        collection = cls.get_collection()
        cart = collection.find_one({'user_id': user_id})
        if cart:
            cart = cls._normalize_cart(cart)
            cart['cart_items'] = [
                item for item in cart['cart_items']
                if str(item.get('book_id')) != book_id
            ]
            collection.update_one(
                {'user_id': user_id},
                {'$set': {'cart_items': cart['cart_items']}}
            )

    @classmethod
    def update_quantity(cls, user_id, book_id, quantity):
        """
        修改购物车中指定商品的数量（最小为1）
        :param user_id: 用户ID
        :param book_id: 图书ID
        :param quantity: 新的商品数量
        :return: 无返回值，直接执行数量更新
        """
        collection = cls.get_collection()
        cart = collection.find_one({'user_id': user_id})
        if cart:
            cart = cls._normalize_cart(cart)
            for item in cart['cart_items']:
                if str(item.get('book_id')) == book_id:
                    item['quantity'] = max(1, int(quantity))
                    break
            collection.update_one(
                {'user_id': user_id},
                {'$set': {'cart_items': cart['cart_items']}}
            )

    @classmethod
    def clear_cart(cls, user_id):
        """
        清空用户购物车（保留购物车文档，仅清空商品列表）
        :param user_id: 用户ID
        :return: 无返回值，直接执行清空
        """
        collection = cls.get_collection()
        collection.update_one(
            {'user_id': user_id},
            {'$set': {'cart_items': []}}
        )

    @classmethod
    def get_item_count(cls, user_id):
        """
        统计用户购物车中所有商品的总数量（数量累加）
        :param user_id: 用户ID
        :return: 购物车商品总数量（整数）
        """
        cart = cls.get_cart(user_id)
        return sum(item.get('quantity', 0) for item in cart.get('cart_items', []))