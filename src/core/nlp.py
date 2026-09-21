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

# Writing tasks — always chat (no Tavily)
WRITING_PATTERNS = [
    "write me", "write a", "write an", "write the",
    "make me a", "make me an",
    "draft a", "draft an",
    "compose a", "compose an",
    "generate a", "generate an",
    "essay", "speech", "letter", "email", "poem", "story",
    "cover letter", "resume",
]

# Recency — always web_search
RECENCY_PATTERNS = [
    "current", "currently", "latest", "newest", "recent", "recently",
    "right now", "today", "tonight", "this week", "this month", "this year",
    "who won", "who is winning", "who leads", "who is leading",
    "release date", "coming out", "when is", "when will", "when does",
    "price of", "cost of", "stock price", "how much is",
    "breaking news", "headlines", "news about", "what's happening",
    "score", "match result", "winner of",
]


def force_intent(command):
    """
    Fast Python-side pre-check.
    Returns intent string ('chat' | 'web_search') or None if unsure.
    """
    lower = command.lower()

    # Writing tasks win — even if they mention "latest"
    if any(w in lower for w in WRITING_PATTERNS):
        return "chat"

    # Recency keywords
    if any(r in lower for r in RECENCY_PATTERNS):
        return "web_search"

    # Any near-future year (2024+)
    if re.search(r"\b(202[4-9]|203[0-9])\b", lower):
        return "web_search"

    return None


# ============================================
# TIER 2: LLM CLASSIFIER
# ============================================

def classify(command):
    # ---- Tier 1: Fast pre-check ----
    forced = force_intent(command)
    if forced == "chat":
        return {"intent": "chat", "entities": {}}
    if forced == "web_search":
        return {"intent": "web_search", "entities": {"query": command}}

    # ---- Tier 2: LLM classification ----
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

    ===================================================
    THE #1 RULE — web_search vs chat
    ===================================================

    Ask yourself: "Could the answer be different today than a year ago?"

    YES → web_search
      - Current leaders, prices, stock, weather
      - Latest versions, releases, updates
      - Who won, who is, what happened
      - Recent events, news, sports results
      - Anything about the present moment

    NO → chat
      - Writing tasks (essay, letter, speech, email, poem, story)
      - Definitions, explanations, how things work
      - Math, coding, philosophy
      - Casual conversation, jokes, advice
      - Timeless knowledge

    EXAMPLES:

    User: "who is the current president of france"    -> web_search
    User: "who won the last fifa world cup"           -> web_search
    User: "latest iphone"                             -> web_search
    User: "current bitcoin price"                     -> web_search
    User: "what's happening in tech today"            -> web_search

    User: "write me an essay on india"                -> chat
    User: "make me a speech for my hackathon"         -> chat
    User: "draft an email to my boss"                 -> chat
    User: "explain how async works in python"         -> chat
    User: "what is quantum physics"                   -> chat
    User: "tell me a joke"                            -> chat
    User: "calculate 5+3"                             -> calculate

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
      "what is my roll number"   -> key="my roll number"

    RULE 5: Multi-key recall -> join with " and ".
      "what is my name and roll number" -> key="my name and roll number"

    RULE 6: "remember this" without content -> chat (nothing to remember).

    ===================================================
    RETURN FORMAT
    ===================================================

    Return ONLY JSON:
    {
        "intent": "one of the above intents",
        "entities": {"key": "value"}
    }

    Examples for entity extraction:

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
