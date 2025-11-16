from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from sqlalchemy.future import select
from sqlalchemy import func


class ProjectModel(BaseDataModel):
    """
    This class handles all the database operations related to projects.
    """

    def __init__(self, db_client: object):
        """
        Initializes the ProjectModel.

        Args:
            db_client (object): The database client.
        """
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Creates an instance of the ProjectModel.

        Args:
            db_client (object): The database client.

        Returns:
            ProjectModel: An instance of the ProjectModel.
        """
        instance = cls(db_client)
        return instance

    async def create_project(self, project: Project):
        """
        Creates a new project in the database.

        Args:
            project (Project): The project to create.

        Returns:
            Project: The created project.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Add the project to the session
                session.add(project)
            await session.commit()
            await session.refresh(project)

        return project

    async def get_or_create_project(self, project_id: int):
        """
        Gets a project from the database or creates a new one if it doesn't exist.

        Args:
            project_id (int): The ID of the project.

        Returns:
            Project: The project.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Select the project with the given ID
                query = select(Project).where(Project.id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                if project is None:
                    # Create a new project if it doesn't exist
                    project_record = Project(id=project_id)
                    project = await self.create_project(project=project_record)
                    return project
                else:
                    return project

    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        """
        Gets all projects from the database with pagination.

        Args:
            page (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The number of projects per page. Defaults to 10.

        Returns:
            A tuple containing a list of projects and the total number of pages.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Get the total number of projects
                total_documents = await session.execute(
                    select(func.count(Project.project_id))
                ).scalar_one()

                total_pages = total_documents // page_size

                if total_documents % page_size > 0:
                    total_pages += 1

                # Select all projects with pagination
                query = select(Project).offset((page - 1) * page_size).limit(page_size)
                projects = await session.execute(query).scalars().all()

                return projects, total_pages
