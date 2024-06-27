from abc import ABC


class Offering(ABC):
    def __init__(self, offering_id: int, name: str) -> None:
        self.offering_id: int = offering_id
        self.name: str = name


class Product(Offering):
    """Represents a product in the e-commerce system."""

    def __init__(
        self, product_id: int, name: str, price: float, stock: int
    ) -> None:
        super().__init__(product_id, name)
        self.price: float = price
        self.stock: int = stock

    def update_stock(self, amount: int) -> None:
        """Updates the stock quantity for the product."""
        self.stock += amount

    def get_product_info(self) -> str:
        """Returns the product's information."""
        return (
            f'Product ID: {self.product_id}, Name: {self.name}, '
            f'Price: ${self.price}, Stock: {self.stock}'
        )


class Service(Offering):
    """Represents a service in the e-commerce system."""

    def __init__(
        self, service_id: int, name: str, rate: float, duration: int
    ) -> None:
        super().__init__(service_id, name)
        self.rate: float = rate
        self.duration: int = duration  # duration in minutes

    def update_duration(self, additional_minutes: int) -> None:
        """Updates the duration for the service."""
        self.duration += additional_minutes

    def get_service_info(self) -> str:
        """Returns the service's information."""
        return (
            f'Service ID: {self.service_id}, Name: {self.name}, '
            f'Rate: ${self.rate}/hr, Duration: {self.duration} minutes'
        )
