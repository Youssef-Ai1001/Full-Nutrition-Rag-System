from pydantic import BaseModel
from typing import Optional


class ProcessRequest(BaseModel):
    """
    This class represents a request to process a file.
    """

    # The ID of the file to process.
    file_id: str = None
    # The size of each chunk.
    chunk_size: Optional[int] = 100
    # The size of the overlap between chunks.
    overlap_size: Optional[int] = 20
    # Whether to reset the collection before processing.
    do_reset: Optional[int] = 0
