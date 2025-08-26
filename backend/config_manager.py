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
            'prompts_file'  # Updated to validate prompts file path instead of inline prompts
        ]
        
        for key in required_keys:
            if not self._get_nested_value(config, key):
                raise ValueError(f"Missing required configuration: {key}")
        
        # Validate that prompts file exists and contains required prompts
        prompts_file = self._get_nested_value(config, 'prompts_file')
        if prompts_file:
            self._validate_prompts_file(prompts_file)
    
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
    
    def _validate_prompts_file(self, prompts_file: str):
        """Validate that prompts file exists and contains required prompts"""
        prompts_path = Path(prompts_file)
        if not prompts_path.is_absolute():
            # If relative path, make it relative to config file directory
            config_dir = Path(self.config_path).parent
            prompts_path = config_dir / prompts_file
        
        if not prompts_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {prompts_path}")
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as file:
                prompts_config = yaml.safe_load(file)
            
            # Validate required prompts exist
            required_prompts = ['prompt_1', 'prompt_2', 'prompt_3']
            for prompt_name in required_prompts:
                if prompt_name not in prompts_config:
                    raise ValueError(f"Missing required prompt '{prompt_name}' in prompts file: {prompts_path}")
        
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in prompts file {prompts_path}: {e}")
    
    def _load_prompts_from_file(self) -> Dict[str, str]:
        """Load prompts from external YAML file"""
        prompts_file = self.config.get('prompts_file')
        if not prompts_file:
            return {}
        
        prompts_path = Path(prompts_file)
        if not prompts_path.is_absolute():
            # If relative path, make it relative to config file directory
            config_dir = Path(self.config_path).parent
            prompts_path = config_dir / prompts_file
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as file:
                prompts_config = yaml.safe_load(file)
            return prompts_config or {}
        except Exception as e:
            print(f"Error loading prompts from {prompts_path}: {e}")
            return {}
    
    def get_prompts(self) -> Dict[str, str]:
        """Get all prompts from external file"""
        return self._load_prompts_from_file()
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get specific prompt by name from external file"""
        prompts = self._load_prompts_from_file()
        return prompts.get(prompt_name, '')
    
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