#!/usr/bin/env python3
"""
skillhelp engine — multi-framework skill discovery, caching, and display.
Supports: Claude, Codex, Cursor, Windsurf, Copilot, Cline.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import textwrap
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── ANSI Colors ──────────────────────────────────────────────
B = "\033[1m"
D = "\033[2m"
C = "\033[36m"
G = "\033[32m"
Y = "\033[33m"
M = "\033[35m"
R = "\033[31m"
RST = "\033[0m"
SEP = "━" * 56

# ── Supported Frameworks ────────────────────────────────────
#   type="directory" → each subdirectory is a skill (Claude, Codex)
#   type="file"      → each file is a skill/rule (Cursor, Windsurf, etc.)
FRAMEWORKS = [
    {"name": "Claude",     "path": ".claude/skills",       "type": "directory"},
    {"name": "Codex",      "path": ".agents/skills",       "type": "directory"},
    {"name": "Cursor",     "path": ".cursor/rules",        "type": "file"},
    {"name": "Windsurf",   "path": ".windsurf/rules",      "type": "file"},
    {"name": "Workflows",  "path": ".windsurf/workflows",  "type": "file"},
    {"name": "Copilot",    "path": ".github/instructions", "type": "file"},
    {"name": "Cline",      "path": ".cline/rules",         "type": "file"},
]


# ── Git Helpers ──────────────────────────────────────────────

def _git(args: list[str], cwd: str) -> str | None:
    try:
        r = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, cwd=cwd,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def find_git_root(cwd: str) -> str | None:
    return _git(["rev-parse", "--show-toplevel"], cwd)


def find_canonical_repo_root(from_dir: str) -> str | None:
    git_common = _git(["rev-parse", "--git-common-dir"], from_dir)
    if git_common is None:
        return None
    if not os.path.isabs(git_common):
        git_common = os.path.join(from_dir, git_common)
    abs_git = os.path.normpath(git_common)
    if abs_git.endswith(os.sep + ".git") or abs_git.endswith("/.git"):
        return abs_git[: -len("/.git")]
    return os.path.dirname(abs_git)


# ── Discovery ───────────────────────────────────────────────

def discover_skills(cwd: str) -> list[tuple[str, dict, str]]:
    """Walk up from CWD, find first directory level with any skill paths.
    Returns list of (base_dir, framework_info, skills_dir).
    """
    current = os.path.abspath(cwd)
    git_root = find_git_root(cwd)

    while True:
        found = []
        for fw in FRAMEWORKS:
            skills_dir = os.path.join(current, fw["path"])
            if not os.path.isdir(skills_dir):
                continue
            entries = os.listdir(skills_dir)
            if fw["type"] == "directory":
                has_content = any(
                    os.path.isdir(os.path.join(skills_dir, e)) for e in entries
                )
            else:
                has_content = any(
                    os.path.isfile(os.path.join(skills_dir, e)) for e in entries
                )
            if has_content:
                found.append((current, fw, skills_dir))

        if found:
            return found

        if git_root and os.path.abspath(current) == os.path.abspath(git_root):
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return []


# ── Hashing ──────────────────────────────────────────────────

def file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes_for_directory(skill_dir: str) -> dict[str, str]:
    hashes = {}
    for root, _dirs, files in os.walk(skill_dir):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, skill_dir)
            hashes[relpath] = file_sha256(fpath)
    return hashes


def hashes_for_file(filepath: str) -> dict[str, str]:
    return {os.path.basename(filepath): file_sha256(filepath)}


# ── Cache ────────────────────────────────────────────────────

def get_cache_dir(base_dir: str, fw_name: str, cache_base: str) -> str:
    canonical = find_canonical_repo_root(base_dir)
    worktree_root = find_git_root(base_dir)

    if canonical and worktree_root:
        rel = os.path.relpath(base_dir, worktree_root)
        cache_key = canonical if rel == "." else os.path.join(canonical, rel)
    else:
        cache_key = os.path.abspath(base_dir)

    cache_key = cache_key.lstrip("/")
    fw_slug = fw_name.lower().replace(" ", "-")
    return os.path.join(cache_base, cache_key, fw_slug)


def load_cache(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def cache_is_valid(cache_file: str, current_hashes: dict[str, str]) -> bool:
    cached = load_cache(cache_file)
    if cached is None:
        return False
    if "oneliner_description" not in cached:
        return False
    return cached.get("file_hashes") == current_hashes


# ── Content Builders ────────────────────────────────────────

def build_dir_content(skill_dir: str, skill_name: str) -> str:
    parts = [f"Skill: {skill_name}", f"Directory: {skill_dir}", ""]
    for root, _dirs, files in os.walk(skill_dir):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, skill_dir)
            parts.append(f"--- File: {relpath} ---")
            try:
                with open(fpath, "r", errors="replace") as f:
                    parts.append(f.read())
            except Exception:
                parts.append("<binary or unreadable>")
            parts.append("")
    return "\n".join(parts)


def build_file_content(filepath: str, skill_name: str) -> str:
    parts = [f"Rule/Skill: {skill_name}", f"File: {filepath}", ""]
    try:
        with open(filepath, "r", errors="replace") as f:
            parts.append(f.read())
    except Exception:
        parts.append("<unreadable>")
    return "\n".join(parts)


# ── LLM API (Gemini + OpenAI) ───────────────────────────────

def call_gemini(prompt: str, api_key: str, model: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent?key={api_key}"
    )
    payload = json.dumps(
        {"contents": [{"parts": [{"text": prompt}]}]}
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body).get("error", {}).get("message", body)
        except json.JSONDecodeError:
            msg = body
        raise RuntimeError(f"Gemini API {e.code}: {msg}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response: {e}") from e


def call_openai(prompt: str, api_key: str, model: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body).get("error", {}).get("message", body)
        except json.JSONDecodeError:
            msg = body
        raise RuntimeError(f"OpenAI API {e.code}: {msg}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected OpenAI response: {e}") from e


def call_llm(prompt: str, api_key: str, model: str) -> str:
    """Unified LLM caller — auto-detects Gemini vs OpenAI from API key."""
    if api_key.startswith("sk-"):
        return call_openai(prompt, api_key, model)
    else:
        return call_gemini(prompt, api_key, model)


# ── Description Generation ──────────────────────────────────

def generate_descriptions(
    content: str, api_key: str, model: str,
) -> tuple[str, str, str]:
    oneliner_prompt = (
        "You are a technical writer. Given the following skill/rule contents, "
        "write a ONE-LINE description (max 15 words) that captures what it does. "
        "Output ONLY the single line, no punctuation at the end, no formatting.\n\n"
        + content
    )
    short_prompt = (
        "You are a technical writer. Given the following skill/rule contents, "
        "write a SHORT description (2-3 sentences, max 100 words) covering: "
        "what it does, what input/parameters the user must provide to run it "
        "(e.g. a conversation ID, a service name, a URL), and what output or "
        "outcome to expect. Be concise. Output ONLY the text.\n\n"
        + content
    )
    medium_prompt = (
        "You are a technical writer. Given the following skill/rule contents, "
        "write a MEDIUM description (4-6 sentences, max 250 words) covering: "
        "what it does, what input/parameters the user must provide (e.g. IDs, "
        "names, URLs, config values), what output or outcome to expect, and any "
        "prerequisites or setup the user should know before running it (e.g. "
        "required tools, access, environment variables). Output ONLY the text.\n\n"
        + content
    )
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {
            "o": pool.submit(call_llm, oneliner_prompt, api_key, model),
            "s": pool.submit(call_llm, short_prompt, api_key, model),
            "m": pool.submit(call_llm, medium_prompt, api_key, model),
        }
        return futs["o"].result(), futs["s"].result(), futs["m"].result()


# ── Enumerate Skills ────────────────────────────────────────

def enumerate_skills(skills_dir: str, fw_type: str) -> list[tuple[str, str]]:
    """Returns [(skill_name, skill_path), ...]."""
    results = []
    for entry in sorted(os.listdir(skills_dir)):
        full = os.path.join(skills_dir, entry)
        if fw_type == "directory" and os.path.isdir(full):
            results.append((entry, full))
        elif fw_type == "file" and os.path.isfile(full):
            results.append((os.path.splitext(entry)[0], full))
    return results


# ── Ensure Cache ─────────────────────────────────────────────

def ensure_cache_for_framework(
    base_dir: str, fw: dict, skills_dir: str,
    cache_base: str, api_key: str, model: str,
) -> str:
    """Ensure caches are fresh for one framework. Returns cache_dir."""
    cache_dir = get_cache_dir(base_dir, fw["name"], cache_base)
    skills = enumerate_skills(skills_dir, fw["type"])

    stale = []
    for name, path in skills:
        cache_file = os.path.join(cache_dir, f"{name}_desc.json")
        hashes = (
            hashes_for_directory(path)
            if fw["type"] == "directory"
            else hashes_for_file(path)
        )
        if not cache_is_valid(cache_file, hashes):
            stale.append((name, path, cache_file, hashes))

    if not stale:
        return cache_dir

    os.makedirs(cache_dir, exist_ok=True)
    print(
        f"\n  {B}{C}Generating{RST} {B}{len(stale)}{RST} "
        f"{fw['name']} description(s)...\n",
        file=sys.stderr,
    )

    def process(args):
        name, path, cfile, hashes = args
        try:
            content = (
                build_dir_content(path, name)
                if fw["type"] == "directory"
                else build_file_content(path, name)
            )
            oneliner, short, medium = generate_descriptions(content, api_key, model)
            data = {
                "skill_name": name,
                "framework": fw["name"],
                "oneliner_description": oneliner,
                "short_description": short,
                "medium_description": medium,
                "file_hashes": hashes,
            }
            with open(cfile, "w") as f:
                json.dump(data, f, indent=2)
            return name, None
        except Exception as e:
            return name, str(e)

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(process, s): s for s in stale}
        for future in as_completed(futures):
            name, error = future.result()
            if error:
                print(f"  {R}✗{RST} {name}: {error}", file=sys.stderr)
            else:
                print(f"  {G}✓{RST} {name}", file=sys.stderr)

    return cache_dir


# ── Display ──────────────────────────────────────────────────

DESC_KEY = {
    "oneliner": "oneliner_description",
    "short": "short_description",
    "long": "medium_description",
}


def display_framework(mode: str, cache_dir: str, fw_name: str) -> int:
    if not os.path.isdir(cache_dir):
        return 0
    cache_files = sorted(f for f in os.listdir(cache_dir) if f.endswith("_desc.json"))
    if not cache_files:
        return 0

    desc_key = DESC_KEY.get(mode, "oneliner_description")
    try:
        tw = min(os.get_terminal_size().columns, 100)
    except (ValueError, OSError):
        tw = 80

    print(f"  {B}{M}{fw_name}{RST}")
    print()

    count = 0
    for fname in cache_files:
        data = load_cache(os.path.join(cache_dir, fname))
        if data is None:
            continue
        count += 1
        name = data["skill_name"]
        desc = data.get(desc_key, "No description available.")
        files = ", ".join(data.get("file_hashes", {}).keys())

        if mode == "oneliner":
            print(f"    {G}{name:<26}{RST} {D}{desc}{RST}")
        else:
            wrapped = textwrap.fill(
                desc, width=tw - 8,
                initial_indent="      ", subsequent_indent="      ",
            )
            print(f"    {B}{G}▸ {name}{RST}")
            print(wrapped)
            print(f"      {D}files: {files}{RST}")
            print()

    if mode == "oneliner":
        print()
    return count


# ── Main Run ─────────────────────────────────────────────────

def run(mode: str, api_key: str, model: str, cache_base: str):
    cwd = os.getcwd()
    found = discover_skills(cwd)

    if not found:
        print(f"\n  {Y}No skills found.{RST}", file=sys.stderr)
        print(f"  Searched from {D}{cwd}{RST} up to git root.\n", file=sys.stderr)
        print("  Supported paths:", file=sys.stderr)
        for fw in FRAMEWORKS:
            print(f"    {D}{fw['path']}/{RST}", file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)

    base_dir = found[0][0]

    # Ensure caches
    cache_dirs = []
    for bd, fw, sd in found:
        cd = ensure_cache_for_framework(bd, fw, sd, cache_base, api_key, model)
        cache_dirs.append((cd, fw["name"]))

    # Header
    headers = {"oneliner": "Skills", "short": "Skills", "long": "Skills (detailed)"}
    print(f"\n  {B}{C}{headers.get(mode, 'Skills')}{RST} {D}in{RST} {B}{base_dir}{RST}")
    print(f"  {D}{SEP}{RST}\n")

    total = 0
    for cd, fw_name in cache_dirs:
        total += display_framework(mode, cd, fw_name)

    print(f"  {D}{SEP}{RST}")
    print(f"  {D}{total} skill(s){RST}\n")


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="skillhelp engine")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run")
    p_run.add_argument("--mode", choices=["oneliner", "short", "long"], default="oneliner")
    p_run.add_argument("--api-key", required=True)
    p_run.add_argument("--model", default="gpt-5.4")
    p_run.add_argument("--cache-base", default=os.path.expanduser("~/.skill-help"))

    args = parser.parse_args()

    if args.command == "run":
        run(args.mode, args.api_key, args.model, args.cache_base)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
