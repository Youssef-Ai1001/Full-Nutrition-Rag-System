import os


class TemplateParser:
    """
    This class parses templates from the locales directory.
    """

    def __init__(self, language: str = None, default_language="en"):
        """
        Initializes the TemplateParser.

        Args:
            language (str, optional): The language to use. Defaults to None.
            default_language (str, optional): The default language to use. Defaults to "en".
        """
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None

        self.set_language(language)

    def set_language(self, language: str):
        """
        Sets the language to use.

        Args:
            language (str): The language to use.
        """
        if not language:
            self.language = self.default_language

        # Check if the language exists, otherwise use the default language
        language_path = os.path.join(self.current_path, "locales", language)
        if language and os.path.exists(language_path):
            self.language = language

        else:
            self.language = self.default_language

    def get(self, group: str, key: str, vars: dict = {}):
        """
        Gets a template from a group.

        Args:
            group (str): The group to get the template from.
            key (str): The key of the template to get.
            vars (dict, optional): A dictionary of variables to substitute in the template. Defaults to {}.

        Returns:
            The template, or None if it doesn't exist.
        """
        if not group or not key:
            return None

        # Get the path to the group file
        group_path = os.path.join(
            self.current_path, "locales", self.language, f"{group}.py"
        )
        targeted_language = self.language
        # If the group file doesn't exist for the current language, use the default language
        if not os.path.exists(group_path):
            group_path = os.path.join(
                self.current_path, "locales", self.default_language, f"{group}.py"
            )
            targeted_language = self.default_language

        if not os.path.exists(group_path):
            return None

        # Import the group module
        module = __import__(
            f"stores.llm.templates.locales.{targeted_language}.{group}",
            fromlist=[group],
        )

        if not module:
            return None

        # Get the template from the module and substitute the variables
        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars)
