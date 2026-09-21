# src/features/summarize.py
from src.features.get import get_active_window

def summarize_active():
    window = get_active_window()
    if window["class"] in ["firefox", "librewolf"]:
        # Get URL from browser history
        url = get_browser_url()
        content = fetch_page_content(url)
    elif window["class"] in ["nvim", "code"]:
        # Read file
        file_path = get_file_path(window)
        content = open(file_path).read()

    # Send to LLM
    return ask_llm(f"Summarize this:\n{content}")
