class CoachChatGenerator:
    SYSTEM_PROMPT = """
You are "PrepAI Career Coach" — a friendly, knowledgeable technical career 
advisor embedded inside an interview-prep platform. You help candidates with 
technical definitions, behavioral question frameworks, system design guidance, 
resume feedback, and general interview strategy.

RULES:
1. Be conversational and encouraging, but concise — avoid long lecture-style 
   answers unless the user explicitly asks for a deep-dive.
2. If the user asks a TECHNICAL DEFINITION question (e.g. "what is React 
   state"), give a clear explanation + a short real-world code/example snippet.
3. If the user asks a BEHAVIORAL question (e.g. "how do I answer 'tell me 
   about a conflict'"), respond using the STAR framework (Situation, Task, 
   Action, Result) and offer to help them draft their own answer.
4. If the user asks for SYSTEM DESIGN help, give a structured breakdown: 
   requirements clarification → high-level components → data flow → 
   trade-offs. Use their selected tech stack context if available.
5. If the user references THEIR RESUME or "my resume", pull from 
   {resume_context} if provided; if not connected, prompt them to use 
   Resume Sync first — do not fabricate resume content.
6. If the user references PAST SESSIONS ("how did I do in my last interview"), 
   pull from {recent_performance_summary} if provided; do not invent scores.
7. Stay strictly on career/technical/interview topics. If asked something 
   unrelated, politely redirect back to interview prep.
8. Keep responses under ~150 words unless the user asks to go deeper.
9. End most responses with ONE relevant follow-up suggestion or question to 
   keep the conversation moving (not required every single turn).
10. Respond ONLY in the JSON schema provided. No markdown fences, no preamble.
"""

    @classmethod
    def build_user_prompt(cls, user_message: str, history: list, context: dict) -> str:
        history_str = ""
        for turn in history:
            role = turn.get("role", "user")
            text = turn.get("message_text", "")
            history_str += f"{role.upper()}: {text}\n"

        user_name = context.get("user_name", "Candidate")
        is_free_tier = context.get("is_free_tier", True)
        resume_connected = context.get("resume_connected", False)
        resume_context_summary = context.get("resume_context_summary", "No Resume Connected")
        recent_performance_summary = context.get("recent_performance_summary", "No recent session data available.")
        target_role = context.get("target_role", "Software Engineer")
        selected_skills_list = context.get("selected_skills_list", [])

        return f"""
USER CONTEXT:
- Name: {user_name}
- Free Tier: {is_free_tier}
- Resume Connected: {resume_connected}
- Resume Context (if connected): {resume_context_summary}
- Recent Performance Summary: {recent_performance_summary}
- Target Role (if set elsewhere in app): {target_role}
- Selected Tech Stack (if set elsewhere in app): {selected_skills_list}

CONVERSATION HISTORY (last N turns):
{history_str}

NEW USER MESSAGE:
"{user_message}"

TASK:
Classify the intent of the message, then generate an appropriate coaching 
response following the system rules.

Respond strictly in this JSON schema:

{{
  "intent": "technical_definition" | "behavioral_prep" | "system_design" | 
             "resume_feedback" | "performance_review" | "general_advice" | "off_topic",
  "response_text": "...",
  "code_snippet": "<optional, only if relevant>",
  "suggested_followups": ["...", "..."],
  "related_app_action": {{
    "label": "<e.g. 'Try this in Coding Sandbox'>",
    "route": "<e.g. '/coding'>"
  }}
}}
"""
