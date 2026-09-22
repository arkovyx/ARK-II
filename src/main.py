import time
import os
import threading
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

from src.core.nlp import classify
from src.core import state
from src.core.command_reader import read_new_commands
from src.features.memory import remember, forget, recall, list_all
from src.features.reminders import (
    add_reminder, add_alarm, list_pending, start_checker
)
from src.features.alarms import parse_time_expression, extract_message
from src.features.news import get_top_headlines, search_news
from src.features.search import web_search
from src.features.get import get_last_browser_url, get_active_window
from src.features.download import download_video
from src.features.git import clone_repo
from src.features.summarize import get_active_content

from src.features.workspace import setup_dev_environment
from src.features.media import watch_show
from src.features.scaffold import scaffold_project

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


def handle_command(command):
    """Central brain — shared by terminal, web, voice."""
    command = command.strip()
    if not command:
        return None

    if command == "clear":
        state.clear_history()
        return "🧹 cleared"

    state.append_history("user", command)
    state.set_status("thinking")

    intent_data = classify(command)
    if not intent_data:
        intent_data = {"intent": "chat", "entities": {}}
    intent = intent_data.get("intent", "chat")
    entities = intent_data.get("entities", {})

    # ============================================
    # INTENT HANDLERS
    # ============================================

    if intent == "time":
        response = time.strftime("%I:%M %p")

    elif intent == "date":
        response = time.strftime("%B %d, %Y")

    elif intent == "time_and_date":
        response = f"{time.strftime('%I:%M %p')} — {time.strftime('%B %d, %Y')}"

    elif intent == "greeting":
        response = "Hello! How can I assist you today?"

    elif intent == "goodbye":
        response = "Goodbye! See you again!"

    elif intent == "thank_you":
        response = "You're welcome!"

    elif intent == "how_are_you":
        response = "I'm doing great! Thanks for asking."

    elif intent == "remember":
        k = entities.get("key", "")
        v = entities.get("value", "")
        response = remember(k, v) if k and v else "Please tell me what to remember."

    elif intent == "recall":
        key = entities.get("key", "")
        if not key:
            response = list_all()
        else:
            result = recall(key)
            response = f"{key} = {result}" if result else f"I don't remember: {key}"

    elif intent == "forget":
        key = entities.get("key", "")
        response = forget(key) if key else "What should I forget?"

    elif intent == "list_memories":
        response = list_all()

    elif intent == "calculate":
        import re
        expr = re.sub(r"[^0-9+\-*/()\s.]", "", command)
        try:
            response = f"Solution: {eval(expr)}"
        except Exception:
            response = "I couldn't calculate that."

    elif intent == "reminder":
        text = entities.get("text", command)
        secs, human = parse_time_expression(text)
        if not secs:
            response = "I couldn't understand the time. Try: 'remind me in 5 minutes to check the oven'"
        else:
            msg = extract_message(text)
            item = add_reminder(msg, secs)
            response = f"⏰ Reminder set: '{msg}' in {human} (id: {item['id']})"

    elif intent == "alarm":
        text = entities.get("text", command)
        secs, human = parse_time_expression(text)
        if not secs:
            response = "I couldn't understand the time. Try: 'set an alarm for 7:30 AM'"
        else:
            msg = extract_message(text)
            item = add_alarm(msg, time.time() + secs)
            response = f"⏱️ Alarm set for {human} (id: {item['id']})"

    elif intent == "list_reminders":
        pending = list_pending()
        if not pending:
            response = "No pending reminders or alarms."
        else:
            lines = ["Pending:"]
            now = time.time()
            for r in pending:
                remaining = int(r["trigger_at"] - now)
                mins = remaining // 60
                secs = remaining % 60
                when = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                icon = "⏰" if r["type"] == "reminder" else "⏱️"
                lines.append(f"  {icon} [{r['id']}] {r['message']} — in {when}")
            response = "\n".join(lines)

    elif intent == "news":
        cmd_lower = command.lower()
        region = "india"
        if "tech" in cmd_lower:
            region = "tech"
        elif "world" in cmd_lower:
            region = "world"
        elif "business" in cmd_lower:
            region = "business"
        elif "science" in cmd_lower:
            region = "science"
        elif "hacker" in cmd_lower or "hn" in cmd_lower:
            region = "hackernews"
        response = get_top_headlines(region=region)

    elif intent == "news_search":
        query = entities.get("query", "")
        if query:
            response = search_news(query)
        else:
            response = "What topic should I search news for?"

    elif intent == "web_search":
        query = entities.get("query", command)
        result, err = web_search(query)
        if err:
            response = err
        else:
            try:
                r = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": (
                            "You are ARK. Use the web search results below to answer "
                            "the user's question. Cite sources by number [1], [2] when "
                            "relevant. Be concise."
                        )},
                        {"role": "user", "content": (
                            f"Question: {query}\n\n"
                            f"Web results:\n{result['context']}"
                        )},
                    ],
                    temperature=0.3,
                    max_tokens=800,
                )
                response = r.choices[0].message.content
            except Exception as e:
                response = f"❌ LLM error: {e}"

    elif intent == "download_current":
        url, title = get_last_browser_url(
            domain_filter="youtube.com",
            max_age_minutes=30,
        )
        if not url:
            url, title = get_last_browser_url(
                domain_filter="youtu.be",
                max_age_minutes=30,
            )
        if not url:
            response = "No browser tab detected. Open a YouTube video first."
        elif "youtube.com" not in url and "youtu.be" not in url:
            response = f"Not a YouTube URL: {url[:60]}"
        else:
            response = download_video(url)

    elif intent == "clone_current":
        url, title = get_last_browser_url(
            domain_filter="github.com",
            max_age_minutes=60,
        )
        if not url:
            response = "No browser tab detected. Open a GitHub repo first."
        elif "github.com" not in url:
            response = f"Not a GitHub URL: {url[:60]}"
        else:
            response = clone_repo(url)

    elif intent == "summarize_current":
        kind, data = get_active_content()
        if kind == "none":
            response = "Couldn't detect what you're looking at."
        elif kind == "url":
            try:
                import requests
                from bs4 import BeautifulSoup
                r = requests.get(
                    data["url"], timeout=8,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                soup = BeautifulSoup(r.content, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                text = soup.get_text(" ", strip=True)[:4000]
                summary_r = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": "Summarize in 3-5 bullet points. Be concise."},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3, max_tokens=500,
                )
                response = summary_r.choices[0].message.content
            except Exception as e:
                response = f"Couldn't fetch page: {e}"
        elif kind == "file":
            try:
                content = Path(data["path"]).read_text()[:4000]
                summary_r = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": "Summarize this file in 3-5 bullet points."},
                        {"role": "user", "content": content}
                    ],
                    temperature=0.3, max_tokens=500,
                )
                response = summary_r.choices[0].message.content
            except Exception as e:
                response = f"Couldn't read file: {e}"

    elif intent == "setup_dev":
        response = setup_dev_environment()

    elif intent == "watch_media":
        response = watch_show(command)

    elif intent == "scaffold_project":
        response = scaffold_project(command)

    else:
        # Fallback: chat with AI
        try:
            r = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": "You are ARK, a helpful AI assistant. Be concise but complete."},
                    {"role": "user", "content": command},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            response = r.choices[0].message.content
        except Exception as e:
            response = f"API Error: {e}"

    state.append_history("ark", response)
    state.set_status("idle")

    return response


def terminal_loop():
    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd == "exit":
                os._exit(0)
            response = handle_command(cmd)
            if response:
                print(f"🤖 {response}\n")
        except (EOFError, KeyboardInterrupt):
            os._exit(0)


def web_poll_loop():
    while True:
        try:
            commands = read_new_commands()
            for cmd in commands:
                print(f"🌐 [web] {cmd}")
                response = handle_command(cmd)
                if response:
                    print(f"🤖 {response}\n")
        except Exception as e:
            print(f"command_reader error: {e}")
        time.sleep(0.5)


def main():
    state.init()
    state.append_history("ark", "ARK online. Type, speak, or use the web UI.")

    start_checker()

    print("""
╔══════════════════════════════════════════╗
║              ARK-II                      ║
║  Terminal: type commands                 ║
║  Web:      http://localhost:8000         ║
╚══════════════════════════════════════════╝
""")

    t1 = threading.Thread(target=web_poll_loop, daemon=True)
    t1.start()

    t2 = threading.Thread(target=terminal_loop, daemon=True)
    t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Bye")


if __name__ == "__main__":
    main()
