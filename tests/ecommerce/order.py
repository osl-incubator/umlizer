from datetime import datetime
from typing import List
from user import User, Address
from offering import Product


class Order:
    """
    Represents an order in the e-commerce system.
    """

    def __init__(self, order_id: int, user: User, address: Address):
        self.order_id: int = order_id
        self.user: User = user
        self.address: Address = address
        self.products: List[Product] = []
        self.order_date: datetime = datetime.now()
        self.is_shipped: bool = False

    def add_product(self, product: Product) -> None:
        """
        Adds a product to the order.
        """
        self.products.append(product)

    def remove_product(self, product_id: int) -> None:
        """
        Removes a product from the order by its ID.
        """
        self.products = [
            product
            for product in self.products
            if product.product_id != product_id
        ]

    def ship_order(self) -> None:
        """
        Marks the order as shipped.
        """
        self.is_shipped = True

    def get_order_summary(self) -> str:
        """
        Returns a summary of the order.
        """
        product_list = ', '.join([product.name for product in self.products])
        return f'Order ID: {self.order_id}, User: {self.user.username}, Products: {product_list}, Shipped: {self.is_shipped}'
