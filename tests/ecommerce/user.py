class User:
    """
    Represents a user in the e-commerce system.
    """

    def __init__(self, user_id: int, username: str, email: str):
        self.user_id: int = user_id
        self.username: str = username
        self.email: str = email

    def get_user_info(self) -> str:
        """
        Returns the user's information.
        """
        return f'User ID: {self.user_id}, Username: {self.username}, Email: {self.email}'


class Address:
    """
    Represents an address in the e-commerce system.
    """

    def __init__(self, street: str, city: str, zipcode: str, user: User):
        self.street: str = street
        self.city: str = city
        self.zipcode: str = zipcode
        self.user: User = user

    def get_full_address(self) -> str:
        """
        Returns the full address as a string.
        """
        return f'{self.street}, {self.city}, {self.zipcode}'
