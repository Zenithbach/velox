# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🏷️ tagger.py — The Librarian
# Extracts keywords, builds YAML frontmatter, generates INDEX.md files.
# Zero dependencies. No API keys. No network calls. Just Python being clever.
#
# "Every good archive needs a cataloger who doesn't take lunch breaks."

import re
from collections import Counter
from datetime import datetime
from pathlib import Path


# ── Stopwords ────────────────────────────────────────────────────────
# Common English words that carry no topical signal.
# Hand-curated because we're not dragging in NLTK for a word list.
# 🧹 Feel free to add more — the longer this list, the better the tags.

STOPWORDS = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "also", "am",
    "an", "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "cant", "could",
    "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down",
    "during", "each", "even", "every", "few", "for", "from", "further", "get",
    "gets", "getting", "go", "going", "gone", "got", "had", "has", "hasnt",
    "have", "havent", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "ill", "im", "in", "into", "is",
    "isnt", "it", "its", "itself", "ive", "just", "know", "let", "lets",
    "like", "ll", "lot", "make", "me", "might", "more", "most", "much", "my",
    "myself", "need", "no", "nor", "not", "now", "of", "off", "oh", "ok",
    "okay", "on", "once", "one", "only", "or", "other", "our", "ours",
    "ourselves", "out", "over", "own", "put", "really", "re", "right", "said",
    "same", "say", "says", "she", "should", "shouldnt", "so", "some", "such",
    "sure", "take", "than", "that", "thats", "the", "their", "theirs", "them",
    "themselves", "then", "there", "theres", "these", "they", "theyre",
    "thing", "things", "think", "this", "those", "through", "to", "too",
    "um", "uh", "up", "us", "use", "used", "using", "ve", "very", "want",
    "was", "wasnt", "way", "we", "well", "were", "werent", "what", "whats",
    "when", "where", "which", "while", "who", "whom", "why", "will", "with",
    "wont", "would", "wouldnt", "you", "your", "youre", "yours", "yourself",
    "yourselves", "youve",
    # 🤖 AI/chat-specific noise words
    "claude", "anthropic", "chat", "message", "response", "conversation",
    "hey", "hi", "hello", "thanks", "thank", "please", "yeah", "yes", "yep",
    "nope", "lol", "haha", "hmm", "alright", "awesome", "cool", "great",
    "good", "nice", "sweet", "okey", "dokey",
})

# Minimum word length to consider as a keyword
MIN_WORD_LENGTH = 3

# Maximum number of tags to extract
MAX_TAGS = 8

# Maximum number of topics to cluster
MAX_TOPICS = 5


def _tokenize(text: str) -> list[str]:
    """
    Break text into lowercase words, strip punctuation.
    Returns only words that pass the stopword and length filters.

    🔬 No regex magic — just split, strip, filter. Boring and reliable.
    """
    # Strip markdown formatting artifacts
    text = re.sub(r'```[\s\S]*?```', ' ', text)   # code blocks
    text = re.sub(r'`[^`]+`', ' ', text)           # inline code
    text = re.sub(r'https?://\S+', ' ', text)      # URLs
    text = re.sub(r'[#*_\[\](){}|>~=+]', ' ', text)  # markdown chars
    text = re.sub(r'---+', ' ', text)              # horizontal rules

    words = []
    for word in text.lower().split():
        # Strip leading/trailing punctuation
        word = word.strip(".,;:!?\"'()-/\\")
        if (
            len(word) >= MIN_WORD_LENGTH
            and word not in STOPWORDS
            and not word.isdigit()
            and word.isalpha()
        ):
            words.append(word)
    return words


def extract_keywords(text: str, max_tags: int = MAX_TAGS) -> list[str]:
    """
    Extract the most distinctive words from text using frequency analysis.
    Returns a list of lowercase hyphenated tags, sorted by frequency.

    This is the budget TF-IDF: we don't have a corpus to compute
    inverse document frequency against, so we just use raw frequency
    with aggressive stopword filtering. Good enough for tagging.

    🏷️ "Not as smart as Haiku, but doesn't cost anything either."
    """
    words = _tokenize(text)
    if not words:
        return []

    counts = Counter(words)

    # Boost compound concepts: if "download" and "organizer" both appear,
    # the hyphenated form is more useful as a tag
    bigrams = []
    for i in range(len(words) - 1):
        bigram = f"{words[i]}-{words[i+1]}"
        bigrams.append(bigram)

    bigram_counts = Counter(bigrams)

    # Only keep bigrams that appear 2+ times — single occurrences are noise
    useful_bigrams = {
        bg: count for bg, count in bigram_counts.items()
        if count >= 2
    }

    # Merge: bigrams get a 1.5x boost since they're more specific
    merged = dict(counts.most_common(max_tags * 3))
    for bg, count in useful_bigrams.items():
        merged[bg] = count * 1.5

    # Sort by score, take the top N
    ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    tags = [word for word, _ in ranked[:max_tags]]

    return tags


def detect_topics(text: str, max_topics: int = MAX_TOPICS) -> list[str]:
    """
    Group the text into broad topic summaries.

    Strategy: split the text into chunks (by markdown headers or paragraph
    breaks), extract the top keyword from each chunk, and deduplicate.
    This gives you a rough "table of contents" for the conversation.

    📚 "Like speed-reading, but without the comprehension anxiety."
    """
    # Split on markdown headers or double newlines
    chunks = re.split(r'\n#{1,3}\s+|\n\n\n+', text)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 50]

    if not chunks:
        # Fallback: just use top keywords as topics
        return extract_keywords(text, max_topics)

    topics = []
    seen = set()
    for chunk in chunks:
        keywords = extract_keywords(chunk, max_tags=2)
        for kw in keywords:
            if kw not in seen:
                topics.append(kw)
                seen.add(kw)
            if len(topics) >= max_topics:
                break
        if len(topics) >= max_topics:
            break

    return topics


def build_frontmatter(
    title: str,
    chat_name: str = "",
    tags: list[str] | None = None,
    topics: list[str] | None = None,
    status: str = "draft",
    source_url: str = "",
    date: str | None = None,
) -> str:
    """
    Build a YAML frontmatter block for a markdown file.

    This is what makes the file searchable in Obsidian, greppable
    in terminal, and self-documenting in any folder.

    📋 "Metadata is a love letter to your future self."
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    lines = ["---"]
    lines.append(f'title: "{_yaml_escape(title)}"')

    if chat_name:
        lines.append(f'chat: "{_yaml_escape(chat_name)}"')

    lines.append(f"date: {date}")

    if tags:
        tag_str = ", ".join(tags)
        lines.append(f"tags: [{tag_str}]")

    if topics:
        lines.append("topics:")
        for topic in topics:
            lines.append(f"  - {topic}")

    lines.append(f"status: {status}")

    if source_url:
        lines.append(f"source: {source_url}")

    lines.append("exported_by: velox")
    lines.append("---")
    lines.append("")  # blank line after frontmatter

    return "\n".join(lines)


def _yaml_escape(text: str) -> str:
    """Escape characters that would break YAML strings."""
    return text.replace('"', '\\"').replace("\n", " ")


def inject_frontmatter(
    filepath: Path,
    chat_name: str = "",
    status: str = "draft",
    source_url: str = "",
) -> bool:
    """
    Read a markdown file, extract tags from its content, and prepend
    YAML frontmatter. Skips files that already have frontmatter.

    Returns True if frontmatter was injected, False if skipped.

    🔖 "Tag it now or grep for it later. Your choice."
    """
    filepath = Path(filepath)

    if not filepath.exists() or filepath.suffix.lower() != ".md":
        return False

    content = filepath.read_text(encoding="utf-8", errors="replace")

    # Skip if already has frontmatter
    if content.strip().startswith("---"):
        return False

    # Extract metadata from content
    title = _extract_title(content, filepath.stem)
    tags = extract_keywords(content)
    topics = detect_topics(content)

    frontmatter = build_frontmatter(
        title=title,
        chat_name=chat_name,
        tags=tags,
        topics=topics,
        status=status,
        source_url=source_url,
    )

    filepath.write_text(frontmatter + content, encoding="utf-8")
    return True


def _extract_title(content: str, fallback: str) -> str:
    """
    Try to find a title from the first markdown header.
    Falls back to the filename (cleaned up).
    """
    for line in content.split("\n")[:10]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    # Clean up filename as title
    return fallback.replace("-", " ").replace("_", " ").title()


def _guess_file_description(filepath: Path) -> str:
    """
    Best-effort description of a non-markdown file based on
    filename patterns and first few lines.

    🔍 "Reading tea leaves, but for filenames."
    """
    name = filepath.name.lower()
    suffix = filepath.suffix.lower()

    # Common patterns
    descriptions = {
        ".py": "Python module",
        ".sh": "Shell script",
        ".toml": "Configuration file",
        ".yml": "YAML configuration",
        ".yaml": "YAML configuration",
        ".json": "JSON data",
        ".txt": "Text file",
        ".css": "Stylesheet",
        ".js": "JavaScript",
        ".html": "HTML document",
        ".jsx": "React component",
        ".ts": "TypeScript",
        ".tsx": "TypeScript React component",
        ".rs": "Rust source",
        ".sql": "SQL query",
        ".csv": "Data file (CSV)",
    }

    base_desc = descriptions.get(suffix, "File")

    # Try to read first comment/docstring for more context
    if filepath.exists() and suffix in {".py", ".sh", ".js", ".ts"}:
        try:
            head = filepath.read_text(encoding="utf-8", errors="replace")[:500]
            for line in head.split("\n"):
                line = line.strip().lstrip("#").lstrip("//").strip()
                if len(line) > 10 and not line.startswith("!"):
                    return f"{base_desc} — {line[:80]}"
        except (OSError, UnicodeDecodeError):
            pass

    return base_desc


def generate_index(
    folder: Path,
    chat_name: str = "",
    source_url: str = "",
    date: str | None = None,
) -> Path:
    """
    Generate an INDEX.md file for a folder of exported chat artifacts.
    This is the "open this first" file — the map, the table of contents,
    the thing that orients you three days later when you've forgotten
    what any of this is.

    Returns the path to the generated INDEX.md.

    📖 "Every folder deserves a tour guide."
    """
    folder = Path(folder)
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    timestamp = datetime.now().strftime("%I:%M %p")

    # Gather all files in the folder (excluding INDEX.md itself)
    files = sorted([
        f for f in folder.iterdir()
        if f.is_file() and f.name != "INDEX.md"
    ])

    # Separate markdown files (we can extract tags from these)
    md_files = [f for f in files if f.suffix.lower() == ".md"]
    other_files = [f for f in files if f.suffix.lower() != ".md"]

    # Collect all tags and topics from markdown files
    all_tags = []
    all_topics = []
    file_table = []

    for md in md_files:
        content = md.read_text(encoding="utf-8", errors="replace")
        tags = extract_keywords(content, max_tags=4)
        all_tags.extend(tags)

        # Determine status from frontmatter if it exists
        status = "reference"
        if "status:" in content:
            for line in content.split("\n"):
                if line.strip().startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                    break

        title = _extract_title(content, md.stem)
        file_table.append((md.name, title, status))

    for other in other_files:
        desc = _guess_file_description(other)
        file_table.append((other.name, desc, "final"))

    # Deduplicate tags
    tag_counts = Counter(all_tags)
    unique_tags = [tag for tag, _ in tag_counts.most_common(MAX_TAGS)]

    # Build topics from all content
    all_content = ""
    for md in md_files:
        all_content += md.read_text(encoding="utf-8", errors="replace") + "\n\n"
    all_topics = detect_topics(all_content) if all_content.strip() else []

    # ── Build the INDEX.md ──────────────────────────────────────────
    display_name = chat_name or folder.name
    lines = []

    # Frontmatter for the index itself
    lines.append(build_frontmatter(
        title=display_name,
        chat_name=chat_name,
        tags=unique_tags,
        topics=all_topics,
        status="index",
        source_url=source_url,
        date=date,
    ))

    lines.append(f"# {display_name}")
    lines.append(f"> Exported from Velox on {date} at {timestamp}")
    lines.append("")

    # Topics section
    if all_topics:
        lines.append("## Topics Covered")
        for topic in all_topics:
            # Make topic names human-readable
            readable = topic.replace("-", " ").title()
            lines.append(f"- **{readable}**")
        lines.append("")

    # File table
    if file_table:
        lines.append("## Files in This Export")
        lines.append("| File | What It Is | Status |")
        lines.append("|------|-----------|--------|")
        for fname, desc, status in file_table:
            lines.append(f"| {fname} | {desc} | {status} |")
        lines.append("")

    # Tags footer
    if unique_tags:
        tag_str = " · ".join(f"`{t}`" for t in unique_tags)
        lines.append(f"**Tags:** {tag_str}")
        lines.append("")

    lines.append("---")
    lines.append("*Indexed by Velox · Built by Claude · Anthropic*")

    index_path = folder / "INDEX.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")

    return index_path
