#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# install-context-menu.sh
# Install a right-click "Convert PDF to Markdown" action for
# common Linux file managers (Nautilus, Nemo, Thunar, Dolphin).
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Detect pdf2md ───────────────────────────────────────────
PDF2MD_BIN="$(command -v pdf2md 2>/dev/null || true)"
if [[ -z "$PDF2MD_BIN" ]]; then
    echo "Error: pdf2md is not installed or not in PATH."
    echo "Install it first:  pip install ."
    exit 1
fi
echo "Found pdf2md at: $PDF2MD_BIN"

# ── Helper: create Nautilus script ──────────────────────────
install_nautilus() {
    local dir="$HOME/.local/share/nautilus/scripts"
    mkdir -p "$dir"

    # Text-only
    cat > "$dir/PDF → Markdown" <<SCRIPT
#!/usr/bin/env bash
# Nautilus script – PDF to Markdown (text only)
IFS=\$'\\n'
for f in \$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    if [[ "\${f,,}" == *.pdf ]]; then
        $PDF2MD_BIN "\$f" 2>&1 | zenity --text-info --title="pdf2md" --width=500 --height=300 || true
    fi
done
SCRIPT
    chmod +x "$dir/PDF → Markdown"

    # With images
    cat > "$dir/PDF → Markdown (with images)" <<SCRIPT
#!/usr/bin/env bash
# Nautilus script – PDF to Markdown (with images)
IFS=\$'\\n'
for f in \$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    if [[ "\${f,,}" == *.pdf ]]; then
        $PDF2MD_BIN --images "\$f" 2>&1 | zenity --text-info --title="pdf2md" --width=500 --height=300 || true
    fi
done
SCRIPT
    chmod +x "$dir/PDF → Markdown (with images)"
    echo "✓ Nautilus scripts installed → $dir"
}

# ── Helper: create Nemo action ──────────────────────────────
install_nemo() {
    local dir="$HOME/.local/share/nemo/actions"
    mkdir -p "$dir"

    cat > "$dir/pdf2md.nemo_action" <<EOF
[Nemo Action]
Name=Convert PDF to Markdown
Comment=Convert PDF to Markdown using Mistral OCR
Exec=bash -c '$PDF2MD_BIN "%F" 2>&1 | zenity --text-info --title="pdf2md" --width=500 --height=300 || true'
Icon-Name=text-x-generic
Selection=s
Extensions=pdf;PDF;
EOF

    cat > "$dir/pdf2md-images.nemo_action" <<EOF
[Nemo Action]
Name=Convert PDF to Markdown (with images)
Comment=Convert PDF to Markdown with images using Mistral OCR
Exec=bash -c '$PDF2MD_BIN --images "%F" 2>&1 | zenity --text-info --title="pdf2md" --width=500 --height=300 || true'
Icon-Name=text-x-generic
Selection=s
Extensions=pdf;PDF;
EOF

    echo "✓ Nemo actions installed → $dir"
}

# ── Helper: create Thunar custom action ─────────────────────
install_thunar() {
    echo "ℹ  Thunar: add a Custom Action manually:"
    echo "   Name:    PDF → Markdown"
    echo "   Command: $PDF2MD_BIN %f"
    echo "   Pattern: *.pdf"
    echo "   Appears: Other Files"
    echo ""
    echo "   For images: $PDF2MD_BIN --images %f"
}

# ── Helper: create Dolphin service menu ─────────────────────
install_dolphin() {
    local dir="$HOME/.local/share/kservices5/ServiceMenus"
    mkdir -p "$dir"

    cat > "$dir/pdf2md.desktop" <<EOF
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=application/pdf;
Actions=pdf2md;pdf2md_images;

[Desktop Action pdf2md]
Name=Convert PDF to Markdown
Exec=$PDF2MD_BIN %f
Icon=text-x-generic

[Desktop Action pdf2md_images]
Name=Convert PDF to Markdown (with images)
Exec=$PDF2MD_BIN --images %f
Icon=text-x-generic
EOF

    echo "✓ Dolphin service menu installed → $dir"
}

# ── Main ────────────────────────────────────────────────────
echo "Installing right-click context menu entries…"
echo ""

install_nautilus
install_nemo
install_dolphin
install_thunar

echo ""
echo "Done!  You may need to restart your file manager for changes to appear."
echo "  nautilus -q   (GNOME Files)"
echo "  nemo -q       (Nemo)"
echo "  dolphin        (re-open)"
