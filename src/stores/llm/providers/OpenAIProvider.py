from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
import logging
from typing import List, Union


class OpenAIProvider(LLMInterface):
    """
    This class provides an interface to the OpenAI API.
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
        Initializes the OpenAIProvider.

        Args:
            api_key (str): The OpenAI API key.
            api_url (str, optional): The OpenAI API URL. Defaults to None.
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

        # Initialize the OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url if self.api_url and len(self.api_url) else None,
        )

        self.enums = OpenAIEnums

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
            self.logger.error(f"OpenAI client is not initialized.")
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

        chat_history.append(self.construct_prompt(prompt, role=OpenAIEnums.USER.value))

        # Generate text using the OpenAI API
        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature,
        )

        if (
            not response
            or not response.choices
            or len(response.choices) == 0
            or not response.choices[0].message
        ):
            self.logger.error("Error while generating text with OpenAI.")
            return None

        return response.choices[0].message.content

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
            self.logger.error(f"OpenAI client is not initialized.")
            return None

        if isinstance(prompt, str):
            prompt = [prompt]

        if not self.embedding_model_id:
            self.logger.error(f"Embedding model is not set.")
            return None

        # Embed the text using the OpenAI API
        response = self.client.embeddings.create(
            model=self.embedding_model_id,
            input=prompt,
        )

        if (
            not response
            or not response.data
            or len(response.data) == 0
            or not response.data[0].embedding
        ):
            self.logger.error("Error while generating embedding with OpenAI.")
            return None

        return [rec.embedding for rec in response.data]

    def construct_prompt(self, prompt: str, role: str):
        """
        Constructs a prompt.

        Args:
            prompt (str): The prompt to construct.
            role (str): The role of the prompt.

        Returns:
            A dictionary containing the role and the prompt.
        """
        return {"role": role, "content": prompt}  # self.process_prompt(prompt)
