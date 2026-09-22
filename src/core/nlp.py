import json
import os
import re
import difflib
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


# ============================================
# FUZZY MATCHING (strict — no short-word noise)
# ============================================

def _word_matches(word, keyword, threshold=0.72):
    word = word.strip(".,!?;:'\"")
    if not word or len(word) < 4:
        return False
    if keyword in word:
        return True
    if abs(len(word) - len(keyword)) > 3:
        return False
    ratio = difflib.SequenceMatcher(None, word, keyword).ratio()
    return ratio >= threshold


def _fuzzy_find(text, keywords, threshold=0.72):
    words = text.split()
    for word in words:
        for kw in keywords:
            if _word_matches(word, kw, threshold):
                return True
    return False


# ============================================
# KEYWORD SETS
# ============================================

WRITING_PATTERNS = [
    "write me", "write a", "write an", "write the",
    "make me a", "make me an",
    "draft a", "draft an",
    "compose a", "compose an",
    "generate a", "generate an",
    "essay", "speech", "letter", "email", "poem", "story",
    "cover letter", "resume",
]

RECENCY_PATTERNS = [
    "current", "currently", "latest", "newest", "recent", "recently",
    "right now", "today", "tonight", "this week", "this month", "this year",
    "who won", "who is winning", "who leads", "who is leading",
    "release date", "coming out", "when is", "when will", "when does",
    "price of", "cost of", "stock price", "how much is",
    "breaking news", "headlines", "news about", "what's happening",
    "score", "match result", "winner of",
]

CLONE_WORDS = ["clone", "cloan", "clown", "clon", "glone"]
REPO_WORDS = ["repo", "repository", "git", "github"]
SUMMARIZE_WORDS = ["summarize", "summarise", "summary", "summrize"]
DOWNLOAD_WORDS = ["download", "downloads"]
VIDEO_WORDS = ["video", "youtube", "vid"]
DEMONSTRATIVES = ["this", "it", "the", "here", "current"]


# ============================================
# TIER 1: FAST PYTHON PRE-CHECK (STRICT PRIORITY)
# ============================================

def force_intent(command):
    lower = command.lower()

    # ---- 1. PROJECT SCAFFOLD (highest priority) ----
    scaffold_phrases = [
        "make a folder named", "make a folder called",
        "create a folder named", "create a folder called",
        "new project named", "new project called",
        "scaffold a project", "setup a new project",
        "set up a new project", "make a new project",
        "create a new project",
    ]
    if any(p in lower for p in scaffold_phrases):
        return "scaffold_project"

    # ---- 2. READ ERROR (screen analysis) ----
    has_read_word = any(w in lower for w in [
        "read this", "read the", "read error", "read screen", "fix it", "anazlyze it", "analyse it",
        "what is this error", "what's this error", "whats this error",
        "explain this error", "explain the error",
        "fix this error", "fix the error", "fix error",
        "solve this error", "resolve this error",
        "analyze this error", "analyse this error",
        "diagnose this error", "diagnose the error",
    ])
    has_error_word = any(w in lower for w in [
        "error", "errors", "exception", "traceback",
        "stack trace", "stacktrace", "bug",
    ])
    has_screen_word = any(w in lower for w in [
        "screen", "this page", "this window",
    ])
    if has_read_word and (has_error_word or has_screen_word):
        return "read_error"

    # ---- 3. DEV WORKSPACE ----
    dev_phrases = [
        "setup my dev environment", "set up my dev environment",
        "setup dev environment", "set up dev environment",
        "start coding", "let's code", "lets code", "coding mode",
        "setup my workspace", "set up my workspace",
        "continue what i was working", "continue where i left",
        "work on the project i was working",
        "yesterday's project", "lets continue working",
        "let's continue working",
        "dev mode", "developer mode", "dev environment",
    ]
    if any(p in lower for p in dev_phrases):
        return "setup_dev"

    # ---- 4. CLONE ----
    has_clone = _fuzzy_find(lower, CLONE_WORDS, threshold=0.7)
    has_repo = _fuzzy_find(lower, REPO_WORDS, threshold=0.7)
    has_this = any(w in lower.split() for w in DEMONSTRATIVES)
    if has_clone and (has_repo or has_this):
        return "clone_current"

    # ---- 5. SUMMARIZE ----
    has_summar = _fuzzy_find(lower, SUMMARIZE_WORDS, threshold=0.75)
    if has_summar and (has_this or "page" in lower or "file" in lower or "article" in lower):
        return "summarize_current"
    if "tldr" in lower or "tl dr" in lower:
        return "summarize_current"

    # ---- 6. DOWNLOAD ----
    has_download = _fuzzy_find(lower, DOWNLOAD_WORDS, threshold=0.75)
    has_video = _fuzzy_find(lower, VIDEO_WORDS, threshold=0.7)
    if has_download and (has_video or has_this):
        return "download_current"

    # ---- 7. WATCH MEDIA ----
    watch_phrases = [
        "let's watch", "lets watch", "play mr robot", "watch mr robot",
        "start mr robot", "continue mr robot", "play the next episode",
        "watch something", "let's watch something",
    ]
    if any(p in lower for p in watch_phrases):
        return "watch_media"
    if re.match(r"^(watch|play)\s+\w", lower) and "video" not in lower and "youtube" not in lower:
        return "watch_media"

    # ---- 8. ACTIVITY REPORT ----
    activity_phrases = [
        "what was i working on", "what have i been working on",
        "what am i working on", "what was i doing",
        "what have i been doing", "what am i doing",
        "activity report", "my activity", "show activity",
        "recent activity", "what did i do today",
    ]
    if any(p in lower for p in activity_phrases):
        return "activity_report"

    # ---- 9. WRITING ----
    if any(w in lower for w in WRITING_PATTERNS):
        return "chat"

    # ---- 10. RECENCY ----
    if any(r in lower for r in RECENCY_PATTERNS):
        return "web_search"

    if re.search(r"\b(202[4-9]|203[0-9])\b", lower):
        return "web_search"

    return None

# ============================================
# TIER 2: LLM CLASSIFIER
# ============================================

def classify(command):
    forced = force_intent(command)
    if forced == "chat":
        return {"intent": "chat", "entities": {}}
    if forced == "web_search":
        return {"intent": "web_search", "entities": {"query": command}}
    if forced in (
        "download_current", "clone_current", "summarize_current",
        "scaffold_project", "setup_dev", "watch_media", "activity_report",
    ):
        return {"intent": forced, "entities": {}}

    system_prompt = """
    You are an intent classifier. Analyze what the user wants and return ONLY a JSON.

    Possible intents:

    1. "time" - current time
    2. "date" - current date
    3. "time_and_date" - both time and date
    4. "greeting" - hello, hi, hey
    5. "goodbye" - bye, goodbye
    6. "thank_you" - thanks
    7. "how_are_you" - how are you
    8. "calculate" - math
    9. "remember" - store info
    10. "recall" - retrieve stored fact
    11. "forget" - delete fact
    12. "list_memories" - list all facts
    13. "reminder" - set reminder
    14. "alarm" - set alarm
    15. "list_reminders" - show reminders
    16. "news" - top headlines
    17. "news_search" - search news about topic
    18. "web_search" - current/factual info from web
    19. "chat" - writing, casual, timeless topics
    20. "download_current" - download the video the user is looking at
    21. "clone_current" - clone the GitHub repo the user is looking at
    22. "summarize_current" - summarize what the user is looking at
    23. "setup_dev" - user wants to start working / set up dev environment
    24. "scaffold_project" - user wants a new Python project scaffolded

    ===================================================
    THE #1 RULE — web_search vs chat
    ===================================================

    Ask: "Could the answer be different today than a year ago?"

    YES -> web_search
    NO  -> chat

    EXAMPLES:

    User: "who is the current president of france"    -> web_search
    User: "latest iphone"                             -> web_search
    User: "write me an essay on india"                -> chat
    User: "explain how async works in python"         -> chat
    User: "tell me a joke"                            -> chat
    User: "calculate 5+3"                             -> calculate

    ===================================================
    ACTIVE WINDOW RULES
    ===================================================

    User: "download this video"        -> download_current
    User: "clone this repo"            -> clone_current
    User: "summarize this page"        -> summarize_current

    ===================================================
    DEV WORKSPACE (setup_dev)
    ===================================================

    User: "setup my dev environment"   -> setup_dev
    User: "let's continue what I was working on" -> setup_dev
    User: "start coding"               -> setup_dev

    ===================================================
    PROJECT SCAFFOLD (scaffold_project)
    ===================================================

    User: "make a folder named X in my dev directory and install Y" -> scaffold_project
    User: "create a new project called test" -> scaffold_project

    ===================================================
    MEMORY RULES
    ===================================================

    RULE 1: Keys must be CONSISTENT.
      "my name" (NOT "name"), "my roll number" (NOT "roll number")

    RULE 2: If user says "my X", key MUST be "my X".

    RULE 3: "remember" -> extract BOTH key and value.
      "remember my name is John" -> key="my name", value="John"

    RULE 4: "recall" -> extract ONLY the key.
      "what is my name" -> key="my name"
      "who am i"        -> key="my name"

    RULE 5: Multi-key -> join with " and ".

    ===================================================
    RETURN FORMAT
    ===================================================

    Return ONLY JSON:
    {
        "intent": "one of the above intents",
        "entities": {"key": "value"}
    }

    Examples:

    User: "remember my name is John" -> {"intent": "remember", "entities": {"key": "my name", "value": "John"}}
    User: "what is my name" -> {"intent": "recall", "entities": {"key": "my name"}}
    User: "forget my name" -> {"intent": "forget", "entities": {"key": "my name"}}
    User: "remind me in 5 minutes to check the oven" -> {"intent": "reminder", "entities": {"text": "remind me in 5 minutes to check the oven"}}
    User: "set an alarm for 7:30 AM" -> {"intent": "alarm", "entities": {"text": "set an alarm for 7:30 AM"}}
    User: "news about AI" -> {"intent": "news_search", "entities": {"query": "AI"}}
    User: "what's the news" -> {"intent": "news", "entities": {}}
    User: "search for rust async runtimes" -> {"intent": "web_search", "entities": {"query": "rust async runtimes"}}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            temperature=0.1,
            max_tokens=200
        )

        content = response.choices[0].message.content
        if content is None:
            return {"intent": "chat", "entities": {}}

        result = json.loads(content.strip())
        return result

    except json.JSONDecodeError:
        return {"intent": "chat", "entities": {}}
    except Exception as e:
        return {"intent": "chat", "entities": {"error": str(e)}}
