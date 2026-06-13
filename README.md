# skillhelp

AI-powered skill browser for coding assistants. Generates concise summaries of skills and rules using OpenAI or Gemini — works with Claude, Codex, Cursor, Windsurf, Copilot, and Cline.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/gndps/skillhelp/main/install.sh | bash
```

Then add the alias to your shell:

```bash
# bash
echo 'alias skillhelp="$HOME/.skillhelp/skillhelp.sh"' >> ~/.bashrc && source ~/.bashrc

# zsh
echo 'alias skillhelp="$HOME/.skillhelp/skillhelp.sh"' >> ~/.zshrc && source ~/.zshrc

# fish
echo 'alias skillhelp "$HOME/.skillhelp/skillhelp.sh"' >> ~/.config/fish/config.fish && source ~/.config/fish/config.fish
```

Set your API key (choose one):

**OpenAI** (recommended):
```bash
# Option 1: Set in .env file
echo 'OPENAI_API_KEY=your_key_here' > ~/.skillhelp/.env

# Option 2: Export as environment variable
export OPENAI_API_KEY=your_key_here
```
Get key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

**Gemini** (free alternative):
```bash
# Option 1: Set in .env file
echo 'GEMINI_API_KEY=your_key_here' > ~/.skillhelp/.env

# Option 2: Export as environment variable
export GEMINI_API_KEY=your_key_here
```
Get key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/gndps/skillhelp/main/uninstall.sh | bash
```

Then remove the `alias skillhelp=...` line from your shell config.

## Usage

Run from any directory inside a project:

```bash
skillhelp            # One-liner descriptions (default)
skillhelp list       # Short descriptions (1-2 sentences)
skillhelp --long     # Detailed descriptions (3-5 sentences)
skillhelp --help     # Show help
```

All command aliases: `list`/`l`/`-l`/`--list`, `long`/`--long`, `help`/`h`/`-h`/`--help`

## Supported Frameworks

| Framework | Path | Type |
|-----------|------|------|
| **Claude** | `.claude/skills/` | Directory-based skills |
| **Codex** | `.agents/skills/` | Directory-based skills |
| **Cursor** | `.cursor/rules/` | File-based rules |
| **Windsurf** | `.windsurf/rules/` | File-based rules |
| **Windsurf Workflows** | `.windsurf/workflows/` | File-based workflows |
| **Copilot** | `.github/instructions/` | File-based instructions |
| **Cline** | `.cline/rules/` | File-based rules |

## How It Works

1. **Walks up** from your current directory looking for skill/rule paths
2. **Stops** at the first directory level containing any definitions (monorepo-friendly)
3. **Generates** one-liner, short, and medium descriptions via OpenAI or Gemini (all in parallel)
4. **Caches** results in `~/.skill-help/` with SHA-256 file hashes
5. **Auto-invalidates** — only regenerates when files actually change
6. **Deduplicates** cache across git worktrees of the same repo

**Default models**: `gpt-5.4` (OpenAI), `gemini-3.5-flash` (Gemini). Override with `OPENAI_MODEL` or `GEMINI_MODEL` in `.env` or as environment variables.
