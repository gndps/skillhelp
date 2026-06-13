#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
#  skillhelp uninstaller
#  Usage: curl -fsSL https://raw.githubusercontent.com/gndps/skillhelp/main/uninstall.sh | bash
# ──────────────────────────────────────────────────────────────

INSTALL_DIR="$HOME/.skillhelp"
CACHE_DIR="$HOME/.skill-help"

B='\033[1m'; G='\033[32m'; Y='\033[33m'; D='\033[2m'; R='\033[31m'; RST='\033[0m'

echo ""
echo -e "  ${B}${R}skillhelp${RST} uninstaller"
echo ""

if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    echo -e "  ${G}✓${RST} Removed ${D}${INSTALL_DIR}${RST}"
else
    echo -e "  ${D}Not found: ${INSTALL_DIR}${RST}"
fi

if [[ -d "$CACHE_DIR" ]]; then
    rm -rf "$CACHE_DIR"
    echo -e "  ${G}✓${RST} Removed cache ${D}${CACHE_DIR}${RST}"
else
    echo -e "  ${D}No cache found${RST}"
fi

echo ""
echo -e "  ${Y}Remember to remove the alias from your shell config:${RST}"
echo ""
echo -e "    ${D}# Remove this line from ~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish${RST}"
echo -e "    ${D}alias skillhelp=...${RST}"
echo ""
