# Providers
PROVIDER_OLLAMA = 'Ollama'
PROVIDER_GEMINI = 'Gemini'
PROVIDER_OPENAI = 'OpenAI'

PROVIDER_CHOICES = [
    (PROVIDER_OLLAMA, 'Ollama'),
    (PROVIDER_GEMINI, 'Gemini'),
    (PROVIDER_OPENAI, 'OpenAI'),
]

# Model Types
MODEL_TYPE_CHAT = 'Chat'
MODEL_TYPE_EMBEDDING = 'Embedding'
MODEL_TYPE_SPEECH = 'Speech'

MODEL_TYPE_CHOICES = [
    (MODEL_TYPE_CHAT, 'Chat'),
    (MODEL_TYPE_EMBEDDING, 'Embedding'),
    (MODEL_TYPE_SPEECH, 'Speech'),
]

# Request Types
REQ_CHAT = 'Chat'
REQ_RESUME_PARSING = 'Resume Parsing'
REQ_QUESTION_GEN = 'Question Generation'
REQ_ANSWER_EVAL = 'Answer Evaluation'
REQ_SPEECH_TRANSCRIPT = 'Speech Transcription'
REQ_ROADMAP_GEN = 'Roadmap Recommendation'

REQ_TYPE_CHOICES = [
    (REQ_CHAT, 'Chat'),
    (REQ_RESUME_PARSING, 'Resume Parsing'),
    (REQ_QUESTION_GEN, 'Question Generation'),
    (REQ_ANSWER_EVAL, 'Answer Evaluation'),
    (REQ_SPEECH_TRANSCRIPT, 'Speech Transcription'),
    (REQ_ROADMAP_GEN, 'Roadmap Recommendation'),
]

# Request Statuses
STATUS_SUCCESS = 'Success'
STATUS_FAILED = 'Failed'
STATUS_PENDING = 'Pending'

STATUS_CHOICES = [
    (STATUS_SUCCESS, 'Success'),
    (STATUS_FAILED, 'Failed'),
    (STATUS_PENDING, 'Pending'),
]
