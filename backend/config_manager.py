"""Configuration management for Resume Automation System"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load environment variables first
        load_dotenv()
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable substitution"""
        try:
            with open(self.config_path, 'r') as file:
                content = file.read()
                
            # Replace environment variables
            content = self._substitute_env_vars(content)
            
            config = yaml.safe_load(content)
            self._validate_config(config)
            
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _substitute_env_vars(self, content: str) -> str:
        """Replace ${VAR_NAME} with environment variable values"""
        import re
        
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Return original if not found
        
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate required configuration keys"""
        required_keys = [
            'anthropic.api_key',
            'google_drive.service_account_file',
            'google_drive.templates_folder_id',
            'google_drive.output_folder_id',
            'prompts.prompt_1',
            'prompts.prompt_2',
            'prompts.prompt_3',
            'prompts.prompt_4'
        ]
        
        for key in required_keys:
            if not self._get_nested_value(config, key):
                raise ValueError(f"Missing required configuration: {key}")
    
    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """Get nested configuration value using dot notation"""
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        value = self._get_nested_value(self.config, key)
        return value if value is not None else default
    
    def get_anthropic_config(self) -> Dict[str, Any]:
        """Get Anthropic API configuration"""
        return self.config.get('anthropic', {})
    
    def get_drive_config(self) -> Dict[str, Any]:
        """Get Google Drive configuration"""
        return self.config.get('google_drive', {})
    
    def get_prompts(self) -> Dict[str, str]:
        """Get all prompts"""
        return self.config.get('prompts', {})
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get specific prompt by name"""
        return self.config.get('prompts', {}).get(prompt_name, '')
    
    def get_file_organization_config(self) -> Dict[str, Any]:
        """Get file organization settings"""
        return self.config.get('file_organization', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system settings"""
        return self.config.get('system', {})
    
    def get_baseline_resume_mapping(self) -> Dict[str, str]:
        """Get baseline resume name to file mapping"""
        return self.config.get('google_drive', {}).get('baseline_resumes', {})
    
    def get_template_mapping(self) -> Dict[str, str]:
        """Get baseline resume mapping (legacy method name for backward compatibility)"""
        return self.get_baseline_resume_mapping()
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()


# Global configuration instance
config = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration instance"""
    return config