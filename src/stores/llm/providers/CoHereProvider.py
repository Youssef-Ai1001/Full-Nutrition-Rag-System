from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum
import cohere
import logging
from typing import List, Union


class CoHereProvider(LLMInterface):
    """
    This class provides an interface to the Cohere API.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = None,
        default_input_max_characters: int = 1000,
        default_generation_max_output_tokens: int = 1000,
        default_generation_temperature: float = 0.5,
    ):
        """
        Initializes the CoHereProvider.

        Args:
            api_key (str): The Cohere API key.
            api_url (str, optional): The Cohere API URL. Defaults to None.
            default_input_max_characters (int, optional): The default maximum number of characters for the input. Defaults to 1000.
            default_generation_max_output_tokens (int, optional): The default maximum number of tokens for the output. Defaults to 1000.
            default_generation_temperature (float, optional): The default temperature for the generation. Defaults to 0.5.
        """
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        # Initialize the Cohere client
        self.client = cohere.Client(api_key=self.api_key)

        self.enums = CoHereEnums

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        """
        Sets the generation model.

        Args:
            model_id (str): The ID of the model to use for generation.
        """
        self.generation_model_id = model_id
        self.logger.info(f"Generation model set to {model_id}")

    def set_embedding_model(self, model_id: str, embedding_size: int):
        """
        Sets the embedding model.

        Args:
            model_id (str): The ID of the model to use for embedding.
            embedding_size (int): The size of the embeddings.
        """
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        self.logger.info(
            f"Embedding model set to {model_id} and embedding size set to {embedding_size}"
        )

    def process_prompt(self, prompt: str):
        """
        Processes a prompt by truncating it to the maximum number of characters.

        Args:
            prompt (str): The prompt to process.

        Returns:
            str: The processed prompt.
        """
        return prompt[: self.default_input_max_characters].strip()

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temperature: float = None,
    ):
        """
        Generates text from a prompt.

        Args:
            prompt (str): The prompt to generate text from.
            chat_history (list, optional): The chat history. Defaults to [].
            max_output_tokens (int, optional): The maximum number of tokens to generate. Defaults to None.
            temperature (float, optional): The temperature to use for generation. Defaults to None.

        Returns:
            The generated text, or None if an error occurred.
        """

        if not self.client:
            self.logger.error(f"CoHere client is not initialized.")
            return None

        if not self.generation_model_id:
            self.logger.error(f"Generation model is not set.")
            return None

        max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self.default_generation_max_output_tokens
        )
        temperature = (
            temperature
            if temperature is not None
            else self.default_generation_temperature
        )

        chat_history.append(self.construct_prompt(prompt, role=CoHereEnums.USER.value))

        # Generate text using the Cohere API
        response = self.client.chat(
            model=self.generation_model_id,
            chat_history=chat_history,
            message=self.process_prompt(prompt),
            temperature=temperature,
            max_tokens=max_output_tokens,
        )

        if not response or not hasattr(response, "text"):
            self.logger.error("Error while generating text with CoHere.")
            return None

        return response.text

    def embed_text(self, prompt: Union[str, List[str]], document_type: str = None):
        """
        Embeds a text.

        Args:
            prompt (Union[str, List[str]]): The text or list of texts to embed.
            document_type (str, optional): The type of the document. Defaults to None.

        Returns:
            The embedded text, or None if an error occurred.
        """

        if not self.client:
            self.logger.error(f"CoHere client is not initialized.")
            return None

        if isinstance(prompt, str):
            prompt = [prompt]

        if not self.embedding_model_id:
            self.logger.error(f"Embedding model is not set.")
            return None

        input_type = CoHereEnums.DOCUMENT.value

        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        # Embed the text using the Cohere API
        response = self.client.embed(
            model=self.embedding_model_id,
            texts=[self.process_prompt(p) for p in prompt],
            input_type=input_type,
            embedding_types=["float"],
        )

        if not response or not hasattr(response, "embeddings"):
            self.logger.error("Error while generating embedding with CoHere.")
            return None

        embeddings = None
        if hasattr(response.embeddings, "float"):
            embeddings = response.embeddings.float
        elif hasattr(response.embeddings, "int8"):
            embeddings = response.embeddings.int8

        if not embeddings or len(embeddings) == 0:
            self.logger.error("Empty embeddings returned from CoHere.")
            return None

        return [f for f in response.embeddings.float]

    def construct_prompt(self, prompt: str, role: str):
        """
        Constructs a prompt.

        Args:
            prompt (str): The prompt to construct.
            role (str): The role of the prompt.

        Returns:
            A dictionary containing the role and the prompt.
        """
        return {"role": role, "text": prompt}  # self.process_prompt(prompt)}
