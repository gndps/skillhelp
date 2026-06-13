#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
#  skillhelp — AI-powered skill browser for AI coding assistants
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_BASE="$HOME/.skill-help"

# Source .env from script directory (only set vars that aren't already set)
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        # Strip surrounding quotes from value
        value="${value%\"}"
        value="${value#\"}"
        # Only set if not already exported in environment
        if ! declare -p "$key" &>/dev/null; then
            export "$key=$value"
        fi
    done < "$SCRIPT_DIR/.env"
fi

# ── Colors ────────────────────────────────────────────────────
B='\033[1m'
D='\033[2m'
C='\033[36m'
G='\033[32m'
Y='\033[33m'
R='\033[31m'
RST='\033[0m'

# ── Help ──────────────────────────────────────────────────────
usage() {
    echo ""
    echo -e "  ${B}${C}skillhelp${RST} — AI-powered skill browser for coding assistants"
    echo ""
    echo -e "  ${B}USAGE${RST}"
    echo -e "    skh ${D}[command]${RST}"
    echo ""
    echo -e "  ${B}COMMANDS${RST}"
    echo -e "    ${G}${B}(default)${RST}            List skills with one-liner descriptions"
    echo -e "    ${G}help${RST}, ${G}-h${RST}, ${G}--help${RST}     Show this help message"
    echo -e "    ${G}list${RST}, ${G}l${RST}, ${G}--list${RST}     List skills with short descriptions"
    echo -e "    ${G}long${RST}, ${G}--long${RST}        List skills with detailed descriptions"
    echo ""
    echo -e "  ${B}SUPPORTED FRAMEWORKS${RST}"
    echo -e "    ${D}Claude${RST} (.claude/skills)    ${D}Codex${RST} (.agents/skills)"
    echo -e "    ${D}Cursor${RST} (.cursor/rules)     ${D}Windsurf${RST} (.windsurf/rules)"
    echo -e "    ${D}Copilot${RST} (.github/instructions)  ${D}Cline${RST} (.cline/rules)"
    echo ""
    echo -e "  ${B}HOW IT WORKS${RST}"
    echo -e "    • Walks up from CWD to find the nearest skill definitions"
    echo -e "    • Supports monorepos — stops at the first level with skills"
    echo -e "    • Uses OpenAI or Gemini to generate concise summaries (cached with hashes)"
    echo -e "    • Cache: ${D}~/.skill-help/${RST}"
    echo ""
    echo -e "  ${B}CONFIG${RST}"
    echo -e "    Set ${Y}OPENAI_API_KEY${RST} or ${Y}GEMINI_API_KEY${RST} in ${D}~/.skillhelp/.env${RST}"
    echo -e "    Or export as environment variables"
    echo -e "    Defaults: ${D}gpt-5.4${RST} (OpenAI), ${D}gemini-3.5-flash${RST} (Gemini)"
    echo ""
}

# ── Run a display mode via Python engine ─────────────────────
run_mode() {
    local mode="$1"
    local api_key=""
    local model=""

    # Auto-detect provider: OpenAI takes precedence if both are set
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        api_key="$OPENAI_API_KEY"
        model="${OPENAI_MODEL:-gpt-5.4}"
    elif [[ -n "${GEMINI_API_KEY:-}" ]]; then
        api_key="$GEMINI_API_KEY"
        model="${GEMINI_MODEL:-gemini-3.5-flash}"
    else
        echo -e "${R}✗ Error:${RST} No API key set." >&2
        echo "" >&2
        echo -e "  ${B}Option 1:${RST} Set in ${D}~/.skillhelp/.env${RST}" >&2
        echo -e "    ${D}echo 'OPENAI_API_KEY=your_key_here' > ~/.skillhelp/.env${RST}" >&2
        echo "" >&2
        echo -e "  ${B}Option 2:${RST} Export as environment variable" >&2
        echo -e "    ${D}export OPENAI_API_KEY=your_key_here${RST}" >&2
        echo "" >&2
        echo -e "  Get keys at:" >&2
        echo -e "    ${Y}OpenAI:${RST} ${D}https://platform.openai.com/api-keys${RST}" >&2
        echo -e "    ${Y}Gemini:${RST} ${D}https://aistudio.google.com/apikey${RST}" >&2
        echo "" >&2
        exit 1
    fi

    python3 "$SCRIPT_DIR/_skill_cache.py" run \
        --mode "$mode" \
        --api-key "$api_key" \
        --model "$model" \
        --cache-base "$CACHE_BASE"
}

# ── Main ─────────────────────────────────────────────────────
main() {
    local cmd="${1:-oneliner}"

    case "$cmd" in
        help|h|-h|--help)    usage ;;
        list|l|-l|--list)    run_mode "short" ;;
        long|--long)         run_mode "long" ;;
        oneliner)            run_mode "oneliner" ;;
        *)
            echo -e "${R}✗ Error:${RST} Unknown command '${cmd}'" >&2
            echo -e "  Run ${G}skh --help${RST} for usage." >&2
            exit 1
            ;;
    esac
}

main "$@"
