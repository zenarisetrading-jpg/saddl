#!/bin/bash
echo "Rolling back Impact Dashboard..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_FILE=$(ls -1 "$SCRIPT_DIR"/impact_dashboard_ORIGINAL_*.py 2>/dev/null | head -1)

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ No backup file found in $SCRIPT_DIR"
    exit 1
fi

echo "Using backup: $BACKUP_FILE"
cp "$BACKUP_FILE" "$DESKTOP_DIR/features/impact_dashboard.py"
echo "✅ Rollback complete. Restart your Streamlit app."
