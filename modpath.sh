modpath() {
    echo ""
    if [ -z "$1" ]; then
        echo "Usage:"
        echo "  modpath <directory> [executable]     # Manual mode"
        echo "  modpath <executable>                 # Auto-discovery mode"
        echo ""
        echo "Examples:"
        echo "  modpath \"/c/Program Files/nodejs\""
        echo "  modpath \"/d/go/bin\" go"
        echo "  modpath node                         # auto-discover mode"
        echo ""
        return 1
    fi

    SEARCH_DIRS=("/c" "/d" "/e" "/f")  # Extend if needed

    # If argument is a directory, manual mode
    if [ -d "$1" ]; then
        DIR="$1"
        BINARY="${2:-node}"
    else
        # Auto-discovery mode
        BINARY="$1"
        FOUND_PATH=""
        for DRIVE in "${SEARCH_DIRS[@]}"; do
            FOUND_PATH=$(find "$DRIVE" -type f -iname "$BINARY.exe" 2>/dev/null | head -n 1)
            if [ -n "$FOUND_PATH" ]; then
                break
            fi
        done

        if [ -z "$FOUND_PATH" ]; then
            echo "❌ '$BINARY.exe' not found in ${SEARCH_DIRS[*]}"
            return 1
        fi

        DIR=$(dirname "$FOUND_PATH")
    fi

    # Add to PATH if not already
    case ":$PATH:" in
        *":$DIR:"*)
            echo "path- $DIR (already in PATH)"
            ;;
        *)
            export PATH="$DIR:$PATH"
            echo "path+ $DIR (added to PATH)"
            ;;
    esac

    # Confirm the binary is now in PATH
    BIN_PATH=$(command -v "$BINARY")
    if [ -x "$BIN_PATH" ]; then
        echo "✅ Found executable '$BINARY' at:"
        echo "path+ $BIN_PATH"
    else
        echo "⚠️ '$BINARY' not found in updated PATH"
    fi
    echo ""
}
modpath




