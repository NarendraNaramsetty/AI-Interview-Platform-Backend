class ATSAuditorGenerator:
    SYSTEM_PROMPT = """
You are "PrepAI ATS Auditor" — an expert resume screener that replicates how 
Applicant Tracking Systems (like Workday, Greenhouse, Taleo) parse and score 
resumes against a target job description or role.

RULES:
1. Score STRICTLY based on the resume text and target role/JD provided — 
   never invent skills, experience, or achievements not present in the text.
2. Evaluate across these weighted categories:
   - Keyword Match (35%): overlap between resume terms and target role's 
     expected tech stack/skills
   - Formatting/ATS-Parseability (20%): section headers, no tables/columns 
     that break parsing, standard fonts implied, no images-as-text
   - Quantified Impact (20%): presence of metrics/numbers in bullet points 
     (e.g. "reduced latency by 40%" vs "improved performance")
   - Structure & Completeness (15%): presence of standard sections (Summary, 
     Experience, Skills, Education, Projects)
   - Action-Verb Strength (10%): use of strong action verbs vs passive phrasing
3. Flag any missing keywords that are commonly expected for the target role 
   but absent in the resume.
4. Do NOT penalize for personal details (age, photo, etc.) — just note if 
   present, since some ATS systems mishandle them.
5. Give specific, actionable recommendations tied to exact resume lines, not 
   generic advice like "add more skills".
6. If no target role/JD is provided, infer the most likely role from resume 
   content and note that assumption explicitly.
7. Respond ONLY in the JSON schema provided. No markdown, no preamble.
"""

    @classmethod
    def build_user_prompt(cls, resume_raw_text: str, target_role_or_jd: str, 
                          file_type: str, file_size_kb: int) -> str:
        role_str = target_role_or_jd if target_role_or_jd else "Not Provided (infer target role)"
        
        return f"""
RESUME TEXT (extracted from uploaded file):
\"\"\"
{resume_raw_text}
\"\"\"

TARGET ROLE / JOB DESCRIPTION (optional, from user's app profile or pasted JD):
{role_str}

FILE METADATA:
- File Type: {file_type}
- File Size: {file_size_kb} KB

TASK:
Perform a full ATS audit of this resume. Calculate an overall ATS Match Score 
(0-100) using the weighted rubric in the system rules, extract matched and 
missing keywords, and give prioritized, specific recommendations.

Respond strictly in this JSON schema:

{{
  "overall_ats_score": 75,
  "inferred_target_role": "Backend Engineer",
  "category_scores": {{
    "keyword_match": 80,
    "formatting_parseability": 75,
    "quantified_impact": 70,
    "structure_completeness": 80,
    "action_verb_strength": 70
  }},
  "keyword_analysis": {{
    "matched_keywords": ["...", "..."],
    "missing_keywords": ["...", "..."],
    "keyword_density_percent": 2.5
  }},
  "formatting_issues": ["...", "..."],
  "recommendations": [
    {{
      "priority": "high",
      "issue": "...",
      "suggestion": "...",
      "example_rewrite": "..."
    }}
  ],
  "detected_sections": ["Summary", "Experience", "Skills", "Education"],
  "missing_sections": ["..."]
}}
"""
