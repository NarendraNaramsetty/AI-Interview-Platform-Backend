from decouple import config

# Default endpoints configurations
OLLAMA_BASE_URL = config('OLLAMA_BASE_URL', default='https://ollama.prepai.com')
QDRANT_HOST = config('QDRANT_HOST', default='qdrant.prepai.com')
QDRANT_PORT = config('QDRANT_PORT', cast=int, default=6333)

# Provider credentials settings
GEMINI_API_KEY = config('GEMINI_API_KEY', default=config('Gemini_API_KEY', default=''))
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
GROQ_API_KEY = config('GROQ_API_KEY', default=config('Groke_API_KEY', default=''))

# Timeouts
DEFAULT_AI_TIMEOUT = config('DEFAULT_AI_TIMEOUT', cast=int, default=30)
