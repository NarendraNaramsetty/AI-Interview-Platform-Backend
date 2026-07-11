import re

class TechKeywordExtractor:
    TECH_DICTIONARY = {
        "frontend": ["react", "vue", "angular", "html", "css", "javascript", "typescript", "tailwind", "redux"],
        "backend": ["django", "python", "node", "express", "go", "java", "spring", "apis", "rest", "graphql", "sql", "postgresql", "mysql"],
        "devops": ["docker", "kubernetes", "aws", "gcp", "azure", "ci/cd", "jenkins", "terraform"],
        "ai_ml": ["machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "ollama", "gemini", "openai"]
    }

    @classmethod
    def extract_keywords(cls, user_text: str) -> dict:
        user_text_lower = user_text.lower() if user_text else ""
        extracted = []
        matched_categories = set()

        for category, keywords in cls.TECH_DICTIONARY.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', user_text_lower):
                    extracted.append(kw)
                    matched_categories.add(category)

        return {
            "keywords": list(set(extracted)),
            "suggested_categories": list(matched_categories)
        }
