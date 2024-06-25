class Product:
    """
    Represents a product in the e-commerce system.
    """

    def __init__(self, product_id: int, name: str, price: float, stock: int):
        self.product_id: int = product_id
        self.name: str = name
        self.price: float = price
        self.stock: int = stock

    def update_stock(self, amount: int) -> None:
        """
        Updates the stock quantity for the product.
        """
        self.stock += amount

    def get_product_info(self) -> str:
        """
        Returns the product's information.
        """
        return f'Product ID: {self.product_id}, Name: {self.name}, Price: ${self.price}, Stock: {self.stock}'
