# Intent definitions for chatbot query routing and analysis

DEFAULT_INTENTS = {
    "HR Interview": {
        "keywords": ["hr", "human resources", "salary", "etiquette", "strength", "weakness", "behavioral"],
        "description": "Questions and preparation strategy for HR and behavioral interviews."
    },
    "Technical Interview": {
        "keywords": ["technical", "coding", "system design", "algorithms", "dsa", "concepts"],
        "description": "General core technical round concepts and queries."
    },
    "Resume Review": {
        "keywords": ["resume", "cv", "ats", "projects", "formatting", "experience", "education"],
        "description": "Help with building, optimizing, and reviewing resumes for job searches."
    },
    "Career Guidance": {
        "keywords": ["career", "guidance", "roadmap", "path", "freshers", "experienced", "transition"],
        "description": "Career growth paths, roadmap advice, and role explanations."
    },
    "Coding Help": {
        "keywords": ["code", "coding", "debugging", "programming", "errors", "syntax"],
        "description": "General code debugging, syntax queries, and programmatic help."
    },
    "Python Help": {
        "keywords": ["python", "django", "flask", "fastapi", "pip", "virtualenv", "decorators"],
        "description": "Python language syntax, framework implementation, and debugging."
    },
    "React Help": {
        "keywords": ["react", "nextjs", "jsx", "hooks", "state", "props", "redux", "router"],
        "description": "React.js frontend library query support, components, and state management."
    },
    "Django Help": {
        "keywords": ["django", "drf", "orm", "models", "serializers", "migrations", "settings"],
        "description": "Django backend framework, APIs, databases, and general architecture."
    },
    "SQL Help": {
        "keywords": ["sql", "mysql", "postgresql", "query", "database", "joins", "index"],
        "description": "Relational database systems, writing queries, optimizations, and schema design."
    },
    "Interview Tips": {
        "keywords": ["tips", "tricks", "prepare", "advice", "cracking", "strategy", "checklist"],
        "description": "Actionable advice, tips, and strategies for cracking interviews."
    },
    "Behavioral Questions": {
        "keywords": ["behavioral", "star method", "conflict", "leadership", "teamwork", "situation"],
        "description": "Scenario-based behavioral questions and appropriate answer frameworks."
    },
    "Communication Skills": {
        "keywords": ["communication", "english", "speaking", "verbal", "soft skills", "confidence"],
        "description": "Improving soft skills, verbal clarity, and mock discussions."
    },
    "Company Preparation": {
        "keywords": ["company", "tcs", "infosys", "amazon", "google", "accenture", "wipro"],
        "description": "Company-specific interview patterns, rounds, and requirements."
    },
    "SSC Preparation": {
        "keywords": ["ssc", "cgl", "chsl", "reasoning", "aptitude", "quant", "syllabus", "government"],
        "description": "Government exam syllabi, general knowledge, reasoning, and quantitative prep."
    },
    "General Career Questions": {
        "keywords": ["placement", "campus", "jobs", "hiring", "apply", "linkedin", "portfolio"],
        "description": "General queries regarding campus placements, networking, and applications."
    }
}
