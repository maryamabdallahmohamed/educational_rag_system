import os
import yaml

class PromptLoader:
    """Handles loading and managing system prompts."""
    
    @staticmethod
    def load_system_prompt(path) -> str:
        """Load system prompt from YAML file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, path)
        prompt_path = os.path.abspath(prompt_path)

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("SYSTEM_PROMPT", "")
        except FileNotFoundError:
            print(f"Warning: Prompt file not found at {prompt_path}")
            return "You are a helpful AI assistant."
        except Exception as e:
            print(f"Error loading prompt: {e}")
            return "You are a helpful AI assistant."

