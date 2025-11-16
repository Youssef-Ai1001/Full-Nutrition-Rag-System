from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """
    An interface for interacting with a large language model.
    """

    @abstractmethod
    def set_generation_model(self, model_id: str):
        """
        Sets the generation model.

        Args:
            model_id (str): The ID of the model to use for generation.
        """
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int):
        """
        Sets the embedding model.

        Args:
            model_id (str): The ID of the model to use for embedding.
            embedding_size (int): The size of the embeddings.
        """
        pass

    @abstractmethod
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
            The generated text.
        """
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = None):
        """
        Embeds a text.

        Args:
            text (str): The text to embed.
            document_type (str, optional): The type of the document. Defaults to None.

        Returns:
            The embedded text.
        """
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        """
        Constructs a prompt.

        Args:
            prompt (str): The prompt to construct.
            role (str): The role of the prompt.

        Returns:
            The constructed prompt.
        """
        pass
