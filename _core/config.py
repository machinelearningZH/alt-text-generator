import yaml
from pathlib import Path
import logging


class Config:
    """Configuration class that loads settings from config.yaml."""

    def __init__(self):
        self._load_yaml_config()
        # Log level as proper logging level object
        self.log_level = getattr(logging, self._yaml_config["logging"]["log_level"])

    def _load_yaml_config(self):
        """Load YAML configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as config_file:
            self._yaml_config = yaml.safe_load(config_file)

    def __getitem__(self, key):
        """Allow dictionary-like access to YAML config."""
        return self._yaml_config[key]

    def get(self, key, default=None):
        """Get a value from YAML config with optional default."""
        return self._yaml_config.get(key, default)


# Create a single instance to be imported by other modules
config = Config()
