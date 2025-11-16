from helpers.config import get_settings


class BaseDataModel:
    """
    This class provides a base for other data models.
    """

    def __init__(self, db_client: str):
        """
        Initializes the BaseDataModel.

        Args:
            db_client (str): The database client.
        """
        self.db_client = db_client
        self.app_setting = get_settings()
