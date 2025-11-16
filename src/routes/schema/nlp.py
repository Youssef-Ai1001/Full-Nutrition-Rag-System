from pydantic import BaseModel
from typing import Optional


class PushRequest(BaseModel):
    """
    This class represents a request to push data to the vector database.
    """

    # Whether to reset the collection before pushing.
    do_reset: Optional[int] = 0


class SearchRequest(BaseModel):
    """
    This class represents a request to search the vector database.
    """

    # The text to search for.
    text: str
    # The maximum number of results to return.
    limit: Optional[int] = 5
