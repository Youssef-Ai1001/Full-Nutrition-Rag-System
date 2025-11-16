from helpers.config import get_settings, Settings
import os
import random
import string


class BaseController:
    """
    This class provides base functionality for other controllers.
    """

    def __init__(self):
        """
        Initializes the BaseController.
        """
        self.app_settings = get_settings()

        # Set the base directory and the files directory
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(self.base_dir, "assets/files")

        # Set the database directory
        self.database_dir = os.path.join(self.base_dir, "assets/database")

    def generate_random_string(self, length: int = 12):
        """
        Generates a random string of a given length.

        Args:
            length (int, optional): The length of the string to generate. Defaults to 12.

        Returns:
            str: The generated string.
        """
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_database_path(self, db_name: str):
        """
        Gets the path to a database.

        Args:
            db_name (str): The name of the database.

        Returns:
            str: The path to the database.
        """
        database_path = os.path.join(self.database_dir, db_name)

        # Create the database directory if it doesn't exist
        if not os.path.exists(database_path):
            os.makedirs(database_path)

        return database_path
