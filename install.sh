#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
#  skillhelp installer
#  Usage: curl -fsSL https://raw.githubusercontent.com/gndps/skillhelp/main/install.sh | bash
# ──────────────────────────────────────────────────────────────

INSTALL_DIR="$HOME/.skillhelp"
RAW_URL="https://raw.githubusercontent.com/gndps/skillhelp/main"

B='\033[1m'; C='\033[36m'; G='\033[32m'; Y='\033[33m'; D='\033[2m'; RST='\033[0m'

echo ""
echo -e "  ${B}${C}skillhelp${RST} installer"
echo ""

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download core files
echo -e "  ${D}Downloading...${RST}"
curl -fsSL "$RAW_URL/skillhelp.sh"      -o "$INSTALL_DIR/skillhelp.sh"
curl -fsSL "$RAW_URL/_skill_cache.py"   -o "$INSTALL_DIR/_skill_cache.py"
curl -fsSL "$RAW_URL/.env.example"      -o "$INSTALL_DIR/.env.example"

chmod +x "$INSTALL_DIR/skillhelp.sh"

# Don't auto-create .env - user should set it manually or use exported env vars
# The .env.example is provided as reference only

echo -e "  ${G}✓${RST} Installed to ${D}${INSTALL_DIR}${RST}"
echo ""

# ── Shell integration instructions ───────────────────────────
echo -e "  ${B}Add to your shell (pick one):${RST}"
echo ""
echo -e "  ${Y}bash${RST}  ${D}(~/.bashrc or ~/.bash_profile)${RST}"
echo -e "    echo 'alias skh=\"\$HOME/.skillhelp/skillhelp.sh\"' >> ~/.bashrc && source ~/.bashrc"
echo ""
echo -e "  ${Y}zsh${RST}   ${D}(~/.zshrc)${RST}"
echo -e "    echo 'alias skh=\"\$HOME/.skillhelp/skillhelp.sh\"' >> ~/.zshrc && source ~/.zshrc"
echo ""
echo -e "  ${Y}fish${RST}  ${D}(~/.config/fish/config.fish)${RST}"
echo -e "    echo 'alias skh \"\$HOME/.skillhelp/skillhelp.sh\"' >> ~/.config/fish/config.fish && source ~/.config/fish/config.fish"
echo ""

# ── API key reminder ─────────────────────────────────────────
echo -e "  ${B}Set your API key (choose one):${RST}"
echo ""
echo -e "  ${Y}OpenAI${RST} (recommended)"
echo -e "    ${D}echo 'OPENAI_API_KEY=your_key_here' > ${INSTALL_DIR}/.env${RST}"
echo -e "    ${D}Get key at: https://platform.openai.com/api-keys${RST}"
echo ""
echo -e "  ${Y}Gemini${RST} (free alternative)"
echo -e "    ${D}echo 'GEMINI_API_KEY=your_key_here' > ${INSTALL_DIR}/.env${RST}"
echo -e "    ${D}Get key at: https://aistudio.google.com/apikey${RST}"
echo ""
