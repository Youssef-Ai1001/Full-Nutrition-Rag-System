from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import re
import os


class DataController(BaseController):
    """
    This class handles all the data-related operations, such as file validation and path generation.
    """

    def __init__(self):
        """
        Initializes the DataController.
        """
        super().__init__()
        self.size_scale = 1048576  # Convert MB to Bytes  1024*1024

    def validate_uploaded_file(self, file: UploadFile):
        """
        Validates an uploaded file.

        Args:
            file (UploadFile): The file to validate.

        Returns:
            A tuple containing a boolean indicating whether the file is valid and a response signal.
        """

        # Check if the file type is allowed
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        # Check if the file size is within the allowed limit
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value

    def generate_unique_file_path(self, orig_file_name: str, project_id: str):
        """
        Generates a unique file path for a given file name and project ID.

        Args:
            orig_file_name (str): The original file name.
            project_id (str): The ID of the project.

        Returns:
            A tuple containing the new file path and the new file name.
        """

        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_file_name(orig_file_name=orig_file_name)

        new_file_path = os.path.join(project_path, random_key + "_" + cleaned_file_name)

        # Keep generating a new file path until a unique one is found
        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path, random_key + "_" + cleaned_file_name
            )

        return new_file_path, random_key + "_" + cleaned_file_name

    def get_clean_file_name(self, orig_file_name: str):
        """
        Cleans a file name by removing special characters and replacing spaces with underscores.

        Args:
            orig_file_name (str): The original file name.

        Returns:
            str: The cleaned file name.
        """

        # remove any special characters, excpet underscore and .
        cleaned_file_name = re.sub(r"{^\w.}", "", orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name
