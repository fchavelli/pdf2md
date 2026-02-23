#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# uninstall-context-menu.sh
# Remove the right-click context menu entries created by
# install-context-menu.sh.
# ─────────────────────────────────────────────────────────────
set -euo pipefail

echo "Removing right-click context menu entries…"

rm -f "$HOME/.local/share/nautilus/scripts/PDF → Markdown"
rm -f "$HOME/.local/share/nautilus/scripts/PDF → Markdown (with images)"
echo "✓ Nautilus scripts removed"

rm -f "$HOME/.local/share/nemo/actions/pdf2md.nemo_action"
rm -f "$HOME/.local/share/nemo/actions/pdf2md-images.nemo_action"
echo "✓ Nemo actions removed"

rm -f "$HOME/.local/share/kservices5/ServiceMenus/pdf2md.desktop"
echo "✓ Dolphin service menu removed"

echo ""
echo "Done!  Restart your file manager for changes to take effect."
