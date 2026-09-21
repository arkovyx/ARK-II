import feedparser


# Free RSS feeds — no API key, no limits
FEEDS = {
    "india":      "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "world":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    "tech":       "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "business":   "https://feeds.bbci.co.uk/news/business/rss.xml",
    "science":    "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "top":        "https://feeds.bbci.co.uk/news/rss.xml",
    "hackernews": "https://hnrss.org/frontpage",
}


def get_top_headlines(region="india", limit=5):
    """Fetch top headlines from a free RSS feed."""
    try:
        feed_url = FEEDS.get(region, FEEDS["india"])
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            return f"❌ No headlines found in feed: {region}"

        source_name = feed.feed.get("title", "Unknown")
        lines = [f"📰 Top {min(limit, len(feed.entries))} headlines ({source_name}):"]
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.get("title", "").strip()
            lines.append(f"  {i}. {title}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ News error: {e}"


def search_news(query, limit=5):
    """Search news by keyword using Google News RSS — global, no key."""
    try:
        q = query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)

        if not feed.entries:
            return f"No news found for: {query}"

        lines = [f"📰 News about '{query}':"]
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.get("title", "").strip()
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source = parts[1] if len(parts) > 1 else "?"
            else:
                source = "?"
            lines.append(f"  {i}. {title}  ({source})")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ News error: {e}"
