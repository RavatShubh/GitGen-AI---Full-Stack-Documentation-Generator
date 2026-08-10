import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Cohere LLM
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    COHERE_MODEL = "command-a-03-2025"  # ✅ RECOMMENDED - Main flagship model
    
    # Voyage Embeddings
    VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
    VOYAGE_MODEL = "voyage-2"        # Options: voyage-2, voyage-large-2, voyage-code-2
    
    # Other
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    TEMP_DIR = "./temp_repos"