from .LLMEnums import LLMEnums
from .providers import OpenAIProvider, CoHereProvider


class LLMProviderFactory:
    """
    A factory class for creating LLM providers.
    """

    def __init__(self, config: dict):
        """
        Initializes the LLMProviderFactory.

        Args:
            config (dict): A dictionary containing the configuration for the LLM providers.
        """
        self.config = config

    def create(self, provider_name: str):
        """
        Creates an LLM provider.

        Args:
            provider_name (str): The name of the provider to create.

        Returns:
            An instance of the LLM provider, or None if the provider is not supported.
        """
        # Create an OpenAI provider
        if provider_name == LLMEnums.OPENAI.value:
            return OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                api_url=self.config.OPENAI_API_URL,
                default_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE,
            )

        # Create a Cohere provider
        elif provider_name == LLMEnums.COHERE.value:
            return CoHereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE,
            )

        return None
