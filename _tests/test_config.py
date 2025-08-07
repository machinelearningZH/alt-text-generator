import unittest
import yaml
import logging
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from _core.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Sample YAML config for testing
        self.sample_config = {
            "logging": {
                "log_level": "DEBUG",
                "log_file": "test.log"
            },
            "api": {
                "openrouter_base_url": "https://test.api.com"
            },
            "llm": {
                "default_model": "test-model",
                "max_workers": 10
            }
        }

    def test_init_loads_config_successfully(self):
        """Test that Config initializes and loads YAML config successfully."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            self.assertEqual(config.log_level, logging.DEBUG)
            self.assertEqual(config["logging"]["log_file"], "test.log")

    def test_init_sets_correct_log_level(self):
        """Test that log_level is correctly converted to logging level object."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL)
        ]
        
        for level_str, expected_level in test_cases:
            config_data = {"logging": {"log_level": level_str}}
            yaml_content = yaml.dump(config_data)
            
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                config = Config()
                self.assertEqual(config.log_level, expected_level)

    def test_getitem_access(self):
        """Test dictionary-like access using [] operator."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            self.assertEqual(config["api"]["openrouter_base_url"], "https://test.api.com")
            self.assertEqual(config["llm"]["default_model"], "test-model")

    def test_getitem_raises_keyerror_for_missing_key(self):
        """Test that accessing non-existent key raises KeyError."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            with self.assertRaises(KeyError):
                _ = config["non_existent_key"]

    def test_get_method_with_existing_key(self):
        """Test get method with existing key."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            result = config.get("api")
            self.assertEqual(result, self.sample_config["api"])

    def test_get_method_with_missing_key_returns_default(self):
        """Test get method with missing key returns default value."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            result = config.get("non_existent_key", "default_value")
            self.assertEqual(result, "default_value")

    def test_get_method_with_missing_key_returns_none(self):
        """Test get method with missing key returns None when no default provided."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            result = config.get("non_existent_key")
            self.assertIsNone(result)

    def test_config_path_resolution(self):
        """Test that config path is correctly resolved relative to module location."""
        yaml_content = yaml.dump(self.sample_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)) as mock_file:
            Config()
            
            # Verify the file was opened with the correct path
            # The config.py file is in _core/ and should resolve to ../config.yaml
            expected_path = Path(__file__).parent.parent / "config.yaml"
            mock_file.assert_called_once_with(expected_path, "r", encoding="utf-8")

    def test_file_not_found_raises_exception(self):
        """Test that FileNotFoundError is raised when config file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError("Config file not found")):
            with self.assertRaises(FileNotFoundError):
                Config()

    def test_invalid_yaml_raises_exception(self):
        """Test that invalid YAML content raises YAMLError."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with self.assertRaises(yaml.YAMLError):
                Config()

    def test_invalid_log_level_raises_exception(self):
        """Test that invalid log level raises AttributeError."""
        config_data = {"logging": {"log_level": "INVALID_LEVEL"}}
        yaml_content = yaml.dump(config_data)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with self.assertRaises(AttributeError):
                Config()

    def test_missing_logging_section_raises_exception(self):
        """Test that missing logging section raises KeyError."""
        config_data = {"api": {"url": "test"}}
        yaml_content = yaml.dump(config_data)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with self.assertRaises(KeyError):
                Config()

    def test_empty_config_file(self):
        """Test behavior with empty config file."""
        with patch("builtins.open", mock_open(read_data="")):
            with self.assertRaises((KeyError, TypeError)):
                Config()

    def test_config_with_nested_structures(self):
        """Test config access with deeply nested structures."""
        nested_config = {
            "logging": {"log_level": "INFO"},
            "deep": {
                "level1": {
                    "level2": {
                        "level3": "deep_value"
                    }
                }
            }
        }
        yaml_content = yaml.dump(nested_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            self.assertEqual(config["deep"]["level1"]["level2"]["level3"], "deep_value")

    def test_config_with_different_data_types(self):
        """Test config with various data types (strings, numbers, lists, booleans)."""
        mixed_config = {
            "logging": {"log_level": "INFO"},
            "string_value": "test_string",
            "integer_value": 42,
            "float_value": 3.14,
            "boolean_value": True,
            "list_value": ["item1", "item2", "item3"],
            "null_value": None
        }
        yaml_content = yaml.dump(mixed_config)
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = Config()
            self.assertEqual(config["string_value"], "test_string")
            self.assertEqual(config["integer_value"], 42)
            self.assertEqual(config["float_value"], 3.14)
            self.assertEqual(config["boolean_value"], True)
            self.assertEqual(config["list_value"], ["item1", "item2", "item3"])
            self.assertIsNone(config["null_value"])


class TestConfigSingleton(unittest.TestCase):
    """Test the singleton config instance."""

    def test_config_instance_import(self):
        """Test that the config instance can be imported."""
        yaml_content = yaml.dump({"logging": {"log_level": "INFO"}})
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            from _core.config import config
            self.assertIsInstance(config, Config)
            self.assertEqual(config.log_level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
