from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from sqlalchemy.future import select


class AssetModel(BaseDataModel):
    """
    This class handles all the database operations related to assets.
    """

    def __init__(self, db_client: object):
        """
        Initializes the AssetModel.

        Args:
            db_client (object): The database client.
        """
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Creates an instance of the AssetModel.

        Args:
            db_client (object): The database client.

        Returns:
            AssetModel: An instance of the AssetModel.
        """
        instance = cls(db_client)
        return instance

    async def create_asset(self, asset: Asset):
        """
        Creates a new asset in the database.

        Args:
            asset (Asset): The asset to create.

        Returns:
            Asset: The created asset.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Add the asset to the session
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        return asset

    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):
        """
        Gets all assets for a given project ID and asset type.

        Args:
            asset_project_id (str): The ID of the project.
            asset_type (str): The type of the asset.

        Returns:
            list: A list of assets.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Select all assets with the given project ID and asset type
                stmt = select(Asset).where(
                    Asset.asset_project_id == asset_project_id,
                    Asset.asset_type == asset_type,
                )

                results = await session.execute(stmt)
                records = results.scalars().all()
        return records

    async def get_asset_record(self, asset_project_id: str, asset_name: str):
        """
        Gets a single asset record from the database.

        Args:
            asset_project_id (str): The ID of the project.
            asset_name (str): The name of the asset.

        Returns:
            Asset: The asset, or None if it doesn't exist.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Select the asset with the given project ID and asset name
                stmt = select(Asset).where(
                    Asset.asset_project_id == asset_project_id,
                    Asset.asset_name == asset_name,
                )
                result = await session.execute(stmt)
                records = result.scalar_one_or_none()
        return records
