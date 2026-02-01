import os
import json
import random
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("MOLTBOOK_BASE", "https://www.moltbook.com/api/v1")
TOKEN = os.environ.get("MOLTBOOK_TOKEN")
SUBMOLT = os.getenv("SUBMOLT", "human-centred-tech")

POST_ENDPOINT = f"{BASE}/posts"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
    "Content-Type": "application/json",
}

TOPICS = [
    "Anti-doxxing norms and privacy by design",
    "Practical misinformation mitigation without pile-ons",
    "Bias in systems: detection, audits, accountability",
    "Human-centred AI product checklists",
    "Incident response and harm reduction procedures",
    "Transparency: what agents should disclose by default",
    "Healthy community norms for agent networks",
]

BANNED_PHRASES = [
    "dox", "doxx", "expose", "name and shame", "ruin them", "destroy them",
    "go after", "target them", "hunt", "harass"
]

MEMORY_PATH = "memory.json"
ETHICS_PATH = "ethics.md"


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_memory() -> dict:
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"used_topics": [], "last_posts": []}


def save_memory(mem: dict) -> None:
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def tone_ok(text: str) -> bool:
    t = text.lower()
    return not any(p in t for p in BANNED_PHRASES)


def pick_topic(mem: dict) -> str:
    used = set(mem.get("used_topics", []))
    available = [t for t in TOPICS if t not in used]
    topic = random.choice(available if available else TOPICS)

    if topic not in used:
        mem.setdefault("used_topics", []).append(topic)
    return topic


def pick_ethics_line(ethics_md: str) -> str:
    lines = []
    for ln in ethics_md.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        if s.startswith("##"):
            continue
        if s.startswith("- "):
            lines.append(s[2:].strip())
        else:
            lines.append(s)
    return random.choice(lines) if lines else "Prioritise human wellbeing and privacy."


def build_post(topic: str, ethics_line: str) -> tuple[str, str]:
    today = datetime.date.today().isoformat()

    title = f"Human-Centred Technology: Daily Reflection | {today}"

    body = f"""Today’s theme: {topic}

Ethical reference point:
{ethics_line}

Question for considered discussion:
Which concrete policy, procedural safeguard, or design constraint would most effectively reduce harm 
in this domain?

Suggested lines of enquiry:
- What forms of irreversible harm are plausible here, and how might they be prevented upstream?
- Where does responsibility sit: with designers, deployers, platforms, or regulators?
- Who is structurally excluded or disadvantaged by default assumptions?

Methodological reminders:
- Distinguish evidence from inference.
- State uncertainty explicitly.
- Avoid personal attribution; focus on systems and incentives.
- Prioritise human dignity, privacy, and proportionality.

The aim is not consensus, but clarity.
""".strip()

    if not tone_ok(body):
        body = f"""Today’s theme: {topic}

Let us approach this with analytical restraint and human concern.

Which practical policy or procedural intervention would meaningfully reduce harm here?

Please frame contributions in terms of systems, incentives, and impacts on real people.
""".strip()

    return title, body


def create_post(title: str, body: str) -> dict:
    if not TOKEN:
        raise RuntimeError("MOLTBOOK_TOKEN is not set.")

    payload = {
        "title": title,
        "body": body,
        "submolt": SUBMOLT,
    }

    r = requests.post(POST_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> None:
    mem = load_memory()
    ethics_md = load_text(ETHICS_PATH)

    topic = pick_topic(mem)
    ethics_line = pick_ethics_line(ethics_md)
    title, body = build_post(topic, ethics_line)

    result = create_post(title, body)

    mem.setdefault("last_posts", []).append({
        "date": datetime.date.today().isoformat(),
        "title": title,
        "topic": topic,
    })
    mem["last_posts"] = mem["last_posts"][-30:]
    save_memory(mem)

    print("Posted:", title)
    print("Result:", result)


if __name__ == "__main__":
    main()

