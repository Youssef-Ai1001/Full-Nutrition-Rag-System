from .BaseController import BaseController
import os


class ProjectController(BaseController):
    """
    This class handles all the project-related operations, such as creating and getting project paths.
    """

    def __init__(self):
        """
        Initializes the ProjectController.
        """
        super().__init__()

    def get_project_path(self, project_id: str):
        """
        Gets the path to a project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            str: The path to the project.
        """
        project_dir = os.path.join(self.files_dir, str(project_id))

        # Create the project directory if it doesn't exist
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        return project_dir
