import json
import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


# ============================================
# TIER 1: FAST PYTHON PRE-CHECK
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

# Active-window actions — always local
ACTIVE_WINDOW_PATTERNS = [
    "download this video", "download this", "save this video",
    "download the video i'm watching", "download the video i am watching",
    "clone this repo", "clone this repository", "clone this",
    "git clone this",
    "summarize this", "summarize this page", "summarize this file",
    "what does this say", "tl dr this", "tldr this",
]


def force_intent(command):
    lower = command.lower()

    # Active-window actions (highest priority)
    if any(p in lower for p in ACTIVE_WINDOW_PATTERNS):
        if "clone" in lower:
            return "clone_current"
        if "summar" in lower or "tl dr" in lower or "tldr" in lower or "what does this say" in lower:
            return "summarize_current"
        return "download_current"

    # Writing tasks
    if any(w in lower for w in WRITING_PATTERNS):
        return "chat"

    # Recency
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
    if forced in ("download_current", "clone_current", "summarize_current"):
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
    20. "download_current" - download the video/page the user is looking at
    21. "clone_current" - clone the GitHub repo the user is looking at
    22. "summarize_current" - summarize what the user is looking at

    ===================================================
    THE #1 RULE — web_search vs chat
    ===================================================

    Ask yourself: "Could the answer be different today than a year ago?"

    YES -> web_search
    NO  -> chat

    EXAMPLES:

    User: "who is the current president of france"    -> web_search
    User: "who won the last fifa world cup"           -> web_search
    User: "latest iphone"                             -> web_search
    User: "current bitcoin price"                     -> web_search

    User: "write me an essay on india"                -> chat
    User: "make me a speech for my hackathon"         -> chat
    User: "explain how async works in python"         -> chat
    User: "what is quantum physics"                   -> chat
    User: "tell me a joke"                            -> chat
    User: "calculate 5+3"                             -> calculate

    ===================================================
    ACTIVE WINDOW RULES (download_current / clone_current / summarize_current)
    ===================================================

    Use these ONLY when the user refers to something they're LOOKING AT
    (with words like "this", "this video", "this repo", "this page"):

    User: "download this video"        -> download_current
    User: "download this"              -> download_current
    User: "save this video"            -> download_current
    User: "clone this repo"            -> clone_current
    User: "clone this repository"      -> clone_current
    User: "summarize this"             -> summarize_current
    User: "summarize this page"        -> summarize_current
    User: "what does this say"         -> summarize_current

    Do NOT use download_current if the user gives an explicit URL.

    ===================================================
    MEMORY RULES (remember / recall / forget)
    ===================================================

    RULE 1: Keys must be CONSISTENT.
    Use the SHORTEST form that identifies the fact.

    GOOD keys:
      "my name"        (NOT "name")
      "my roll number" (NOT "roll number")
      "my project"     (NOT "project")
      "my address"     (NOT "address")
      "my age"         (NOT "age")
      "my email"       (NOT "email")

    RULE 2: If user says "my X", the key MUST be "my X".

    RULE 3: "remember" -> extract BOTH key and value.
      "remember my name is John"        -> key="my name", value="John"
      "my name is John, remember this"  -> key="my name", value="John"
      "remember I use Neovim"           -> key="editor", value="Neovim"

    RULE 4: "recall" -> extract ONLY the key.
      "what is my name"          -> key="my name"
      "who am i"                 -> key="my name"
      "whoami"                   -> key="my name"

    RULE 5: Multi-key recall -> join with " and ".

    RULE 6: "remember this" without content -> chat.

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
    User: "download this video" -> {"intent": "download_current", "entities": {}}
    User: "clone this repo" -> {"intent": "clone_current", "entities": {}}
    User: "summarize this" -> {"intent": "summarize_current", "entities": {}}
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
