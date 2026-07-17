from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from django.db.models import Q
from .models import Category, ChatSession, ChatMessage, KnowledgeBase, Feedback, AdminAnalytics
from .utils import (
    clean_sentence,
    extract_keywords,
    remove_special_characters,
    remove_extra_spaces,
    convert_lowercase,
    calculate_percentage
)
from ai_core.services import AIService

# Standalone functions

def normalize_text(text: str) -> str:
    """
    Clean sentence using lowercasing, special character removal, and space normalization.
    """
    return clean_sentence(text)

def remove_stop_words(text: str) -> list:
    """
    Remove stop words and return list of key tokens.
    """
    return extract_keywords(text)

def tokenize(text: str) -> list:
    """
    Split normalized text into word tokens.
    """
    return clean_sentence(text).split()

def calculate_similarity(query_tokens: list, kb_tokens: list) -> float:
    """
    Calculate Jaccard similarity score between query tokens and KB tokens.
    """
    if not query_tokens or not kb_tokens:
        return 0.0
    q_set = set(query_tokens)
    k_set = set(kb_tokens)
    intersection = q_set.intersection(k_set)
    union = q_set.union(k_set)
    return float(len(intersection)) / len(union)

def find_best_match(query: str) -> tuple:
    """
    Perform exact keyword, synonym, and token similarity match over active KnowledgeBase.
    Returns (best_match_entry, confidence_score) or (None, 0.0).
    """
    query_keywords = extract_keywords(query)
    query_tokens = clean_sentence(query).split()

    if not query_tokens:
        return None, 0.0

    from django.db.models import Q
    filter_q = Q()
    for token in query_keywords:
        if len(token) > 2:
            filter_q |= Q(keywords__icontains=token) | Q(synonyms__icontains=token) | Q(tags__icontains=token) | Q(question__icontains=token) | Q(title__icontains=token)

    if filter_q:
        active_kb = KnowledgeBase.objects.filter(is_active=True).filter(filter_q).select_related('category')
    else:
        active_kb = KnowledgeBase.objects.filter(is_active=True).select_related('category')
    best_entry = None
    max_score = 0.0

    for entry in active_kb:
        # Parse entry keywords (comma-separated, split into individual word tokens)
        entry_kw_list = []
        for kw in entry.keywords.split(','):
            if kw.strip():
                entry_kw_list.extend(extract_keywords(kw))

        # Parse entry synonyms (comma-separated, split into individual word tokens)
        entry_syn_list = []
        for syn in entry.synonyms.split(','):
            if syn.strip():
                entry_syn_list.extend(extract_keywords(syn))
        
        # Tokenize question, title, category name, and tags
        q_tokens = extract_keywords(entry.question)
        t_tokens = extract_keywords(entry.title)
        c_tokens = extract_keywords(entry.category.name)
        tag_tokens = [clean_sentence(t) for t in entry.tags.split(',') if t.strip()]

        # 1. Exact Keyword match overlap
        kw_match = set(query_keywords).intersection(set(entry_kw_list))
        # 2. Synonym match overlap
        syn_match = set(query_keywords).intersection(set(entry_syn_list))
        
        # Calculate overlap score based on keyword coverage
        matched_kw_count = len(kw_match)
        matched_syn_count = len(syn_match.difference(kw_match))
        
        overlap_score = 0.0
        if query_keywords:
            overlap_score = (matched_kw_count * 1.0 + matched_syn_count * 0.8) / len(query_keywords)
        
        # 3. Partial Token Similarity (Jaccard)
        q_similarity = calculate_similarity(query_tokens, q_tokens)
        t_similarity = calculate_similarity(query_tokens, t_tokens)
        c_similarity = calculate_similarity(query_tokens, c_tokens)
        tag_similarity = calculate_similarity(query_tokens, tag_tokens)

        # Compute final composite score
        # Priority: Exact keyword (1.0 weight) > Synonym (0.8 weight) > Question (0.7) > Title (0.6) > Category/Tags (0.5)
        entry_score = max(
            overlap_score,
            q_similarity * 0.7,
            t_similarity * 0.6,
            c_similarity * 0.5,
            tag_similarity * 0.5
        )

        if entry_score > max_score:
            max_score = entry_score
            best_entry = entry

    # Clamp max_score to 1.0
    max_score = min(max_score, 1.0)
    return best_entry, max_score

def find_local_answer(query: str) -> tuple:
    """
    Lookup local knowledge base. Returns (answer, priority, confidence, source, matched_entry)
    """
    threshold = getattr(settings, 'CHATBOT_CONFIDENCE_THRESHOLD', 0.5)
    best_entry, confidence = find_best_match(query)

    if best_entry and confidence >= threshold:
        return best_entry.answer, best_entry.priority, confidence, 'LOCAL', best_entry
    return None, 0, 0.0, None, best_entry

def call_gemini(query: str) -> str:
    """
    Fallback call to Gemini API (or configured default provider).
    """
    try:
        res = AIService.route_request("Chat", query)
        return res.get("response", "No AI response received.")
    except Exception as e:
        return f"AI connection error: {str(e)}"

def save_message(session, sender: str, message: str, response_source: str = None, confidence_score: float = None) -> ChatMessage:
    """
    Persist chat message to database.
    """
    return ChatMessage.objects.create(
        session=session,
        sender=sender,
        message=message,
        response_source=response_source,
        confidence_score=confidence_score
    )

def create_session(user, title: str = None) -> ChatSession:
    """
    Create a new ChatSession.
    """
    if not title:
        title = "New Chat Session"
    return ChatSession.objects.create(user=user, session_title=title)

def generate_title(message: str) -> str:
    """
    Generate session title from first message.
    """
    words = message.split()
    title = " ".join(words[:5])
    if len(title) > 50:
        title = title[:47] + "..."
    return title or "New Chat Session"

def store_feedback(user, message_id: int, rating: int, comment: str) -> Feedback:
    """
    Store chat feedback.
    """
    msg = ChatMessage.objects.get(pk=message_id)
    return Feedback.objects.create(
        user=user,
        message=msg,
        rating=rating,
        comment=comment
    )

def get_chat_history(session_id: int, user) -> ChatMessage.objects:
    """
    Get messages for a specific session belonging to user.
    """
    return ChatMessage.objects.filter(session_id=session_id, session__user=user).order_by('created_at')


# Class wrapper for views compatibility

class ChatbotService:
    """
    Compat class encapsulating chat session management and message pipelines.
    """

    @classmethod
    def start_chat_session(cls, title: str, user) -> ChatSession:
        return create_session(user, title)

    @classmethod
    def send_message(cls, session_id: int, user_message: str, user) -> ChatMessage:
        """
        Processes query flow: Local neon db lookup -> Gemini fallback -> log analytics -> save messaging.
        """
        try:
            session = ChatSession.objects.get(pk=session_id, user=user)
        except ChatSession.DoesNotExist:
            raise ValidationError("Chat session not found.")

        if not session.is_active:
            raise ValidationError("Cannot send messages to an inactive session.")

        with transaction.atomic():
            # 1. Save user message
            save_message(session, sender='USER', message=user_message)

            # Auto-rename session if it has default title
            if session.session_title == "New Chat Session" or session.session_title == "General Chat Session":
                session.session_title = generate_title(user_message)
                session.save()

            # 2. Search local DB
            local_ans, priority, confidence, source, best_entry = find_local_answer(user_message)

            if local_ans:
                ai_text = local_ans
                response_source = source
                confidence_score = confidence
                was_matched = True
            else:
                # 3. Fallback to Gemini/LLM
                ai_text = call_gemini(user_message)
                # Resolve provider name dynamically from settings/db
                provider = "GEMINI"
                try:
                    from ai_core.models import AIProvider
                    active_prov = AIProvider.objects.filter(is_default=True, is_active=True).first()
                    if active_prov:
                        provider = active_prov.provider_name.upper()
                except Exception:
                    pass
                response_source = provider
                confidence_score = 0.0
                was_matched = False

            # 4. Create database analytics log entry (in Neon PostgreSQL)
            AdminAnalytics.objects.create(
                query=user_message,
                matched_knowledge=best_entry if was_matched else None,
                was_matched=was_matched,
                confidence_score=confidence_score if was_matched else 0.0,
                response_source=response_source
            )

            # 5. Save bot message
            bot_msg = save_message(
                session=session,
                sender='BOT',
                message=ai_text,
                response_source=response_source,
                confidence_score=confidence_score
            )

        return bot_msg

    @classmethod
    def delete_session(cls, session_id: int, user) -> ChatSession:
        try:
            session = ChatSession.objects.get(pk=session_id, user=user)
        except ChatSession.DoesNotExist:
            raise ValidationError("Chat session not found.")

        session.is_active = False
        session.save()
        return session
