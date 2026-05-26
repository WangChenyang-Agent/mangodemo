from extensions import get_mongo


class CartService:
    @staticmethod
    def get_collection():
        return get_mongo()['carts']

    @classmethod
    def get_cart(cls, user_id):
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
        """Migrate old 'items' key to 'cart_items'."""
        if 'items' in cart and 'cart_items' not in cart:
            cart['cart_items'] = cart.pop('items')
        if 'cart_items' not in cart:
            cart['cart_items'] = []
        return cart

    @classmethod
    def add_item(cls, user_id, book):
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
        collection = cls.get_collection()
        collection.update_one(
            {'user_id': user_id},
            {'$set': {'cart_items': []}}
        )

    @classmethod
    def get_item_count(cls, user_id):
        cart = cls.get_cart(user_id)
        return sum(item.get('quantity', 0) for item in cart.get('cart_items', []))
