import re

# Simple list of English stop words
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'cant', 'cannot', 'could',
    'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent', 'having', 'he', 'hed', 'hell', 'hes',
    'her', 'here', 'heres', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im',
    'ive', 'if', 'in', 'into', 'is', 'isnt', 'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my',
    'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours',
    'ourselves', 'out', 'over', 'own', 'same', 'shant', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt',
    'so', 'some', 'such', 'than', 'that', 'thats', 'the', 'their', 'theirs', 'them', 'themselves', 'then',
    'there', 'theres', 'these', 'they', 'theyd', 'theyll', 'theyre', 'theyve', 'this', 'those', 'through',
    'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasnt', 'we', 'wed', 'well', 'were', 'weve', 'werent',
    'what', 'whats', 'when', 'whens', 'where', 'wheres', 'which', 'while', 'who', 'whos', 'whom', 'why', 'whys',
    'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve', 'your', 'yours', 'yourself',
    'yourselves'
}

def remove_special_characters(text: str) -> str:
    """
    Remove punctuation and special characters from text, leaving alphanumeric and spaces.
    """
    if not text:
        return ""
    return re.sub(r'[^\w\s]', '', text)

def remove_extra_spaces(text: str) -> str:
    """
    Replace multiple whitespace characters with a single space and strip boundaries.
    """
    if not text:
        return ""
    return " ".join(text.split())

def convert_lowercase(text: str) -> str:
    """
    Convert text string to lowercase.
    """
    if not text:
        return ""
    return text.lower()

def extract_keywords(text: str) -> list:
    """
    Clean sentence and extract non-stopwords/keywords.
    """
    if not text:
        return []
    cleaned = clean_sentence(text)
    words = cleaned.split()
    return [word for word in words if word not in STOP_WORDS]

def calculate_percentage(score: float) -> float:
    """
    Convert 0-1 similarity score to a 0-100 percentage.
    """
    return round(score * 100.0, 2)

def clean_sentence(text: str) -> str:
    """
    Apply standard lowercase conversion, special character removal, and space normalization.
    """
    if not text:
        return ""
    lowered = convert_lowercase(text)
    no_special = remove_special_characters(lowered)
    return remove_extra_spaces(no_special)
