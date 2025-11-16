from enum import Enum


class LLMEnums(Enum):
    """
    This enum represents the supported LLM providers.
    """

    OPENAI = "OPENAI"
    COHERE = "COHERE"


class OpenAIEnums(Enum):
    """
    This enum represents the roles in the OpenAI API.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class CoHereEnums(Enum):
    """
    This enum represents the roles and document types in the Cohere API.
    """

    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"

    DOCUMENT = "search_document"
    QUERY = "search_query"


class DocumentTypeEnum(Enum):
    """
    This enum represents the type of a document.
    """

    DOCUMENT = "document"
    QUERY = "query"
