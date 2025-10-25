"""
Configuration Management for Resume AI v2
Loads settings from .env file and provides typed access
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class Config(BaseModel):
    """Type-safe configuration settings"""
    
    # API Keys
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    google_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    
    # File Paths
    database_path: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_PATH", 
            r"C:\Users\keith\OneDrive\Desktop\CODE\keith_resume_database.json"
        )
    )
    applications_folder: str = Field(
        default_factory=lambda: os.getenv(
            "APPLICATIONS_FOLDER",
            r"C:\Users\keith\Dropbox\Resume"
        )
    )
    instructions_folder: str = Field(
        default_factory=lambda: os.getenv(
            "INSTRUCTIONS_FOLDER",
            r"C:\Users\keith\OneDrive\Desktop\CODE\resume-optimization\assistant-instructions"
        )
    )
    
    # Vector Database
    chroma_persist_dir: str = Field(
        default_factory=lambda: os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    )
    embedding_model: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    
    # Generation Settings
    default_ai_model: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_AI_MODEL", "claude-sonnet-4-5-20250929")
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.2"))
    )
    max_tokens: int = Field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "60000"))
    )
    
    # Retrieval Settings
    top_k_experiences: int = Field(
        default_factory=lambda: int(os.getenv("TOP_K_EXPERIENCES", "8"))
    )
    top_k_projects: int = Field(
        default_factory=lambda: int(os.getenv("TOP_K_PROJECTS", "6"))
    )
    min_relevance_score: float = Field(
        default_factory=lambda: float(os.getenv("MIN_RELEVANCE_SCORE", "0.3"))
    )
    
    # Validation Settings
    strict_validation: bool = Field(
        default_factory=lambda: os.getenv("STRICT_VALIDATION", "true").lower() == "true"
    )
    flag_unknown_sources: bool = Field(
        default_factory=lambda: os.getenv("FLAG_UNKNOWN_SOURCES", "true").lower() == "true"
    )
    allow_minor_paraphrasing: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_MINOR_PARAPHRASING", "true").lower() == "true"
    )
    
    class Config:
        arbitrary_types_allowed = True
    
    def validate_setup(self) -> tuple[bool, list[str]]:
        """
        Validate that required configuration is present
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check API keys (at least one required)
        if not any([self.anthropic_api_key, self.openai_api_key, self.google_api_key]):
            errors.append("No API key found. Please set at least one: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY")
        
        # Check database file exists
        if not Path(self.database_path).exists():
            errors.append(f"Database file not found: {self.database_path}")
        
        # Check applications folder exists
        if not Path(self.applications_folder).exists():
            errors.append(f"Applications folder not found: {self.applications_folder}")
        
        return len(errors) == 0, errors
    
    def get_primary_api_key(self) -> tuple[str, str]:
        """
        Get the first available API key and its provider
        Returns: (provider_name, api_key)
        """
        if self.anthropic_api_key:
            return "anthropic", self.anthropic_api_key
        elif self.openai_api_key:
            return "openai", self.openai_api_key
        elif self.google_api_key:
            return "google", self.google_api_key
        else:
            raise ValueError("No API key available")

# Global config instance
config = Config()

# Convenience function for validation
def validate_config() -> None:
    """Validate configuration and exit if invalid"""
    is_valid, errors = config.validate_setup()
    if not is_valid:
        print("❌ Configuration Error:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease check your .env file and ensure all required settings are present.")
        exit(1)
    print("✅ Configuration validated successfully")
