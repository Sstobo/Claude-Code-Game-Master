#!/bin/bash
# install.sh - DM Claude Setup Script (zero to hero)
# Installs ALL dependencies for a fresh machine, then sets up the project.
#
# Usage:
#   ./install.sh          Interactive installation with prompts
#   ./install.sh --auto   Non-interactive (installs everything, full extras)
#
# What it installs (if missing):
#   - Homebrew (macOS only)
#   - Python 3.11+
#   - uv (fast Python package manager)
#   - jq (JSON processor used by tools)
#   - All Python dependencies from pyproject.toml
#   - Claude Code (npm package) — if Node.js is available

set -e

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
AUTO_MODE=false
if [ "$1" = "--auto" ]; then
    AUTO_MODE=true
fi

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
if [ -t 1 ] && [ "${TERM}" != "dumb" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    DIM='\033[2m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; DIM=''; NC=''
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
print_header() {
    echo
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo -e "${BOLD}${BLUE}          DM Claude — Setup Script${NC}"
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo
}

step() {
    echo
    echo -e "${BOLD}── $1 ──${NC}"
}

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
err()  { echo -e "  ${RED}✗${NC} $1" >&2; }
info() { echo -e "  ${DIM}$1${NC}"; }

confirm() {
    # In auto mode always say yes
    if [ "$AUTO_MODE" = true ]; then return 0; fi
    local prompt="$1"
    echo -n -e "  ${prompt} [Y/n]: "
    read -r response
    [[ ! "$response" =~ ^[Nn]$ ]]
}

# ---------------------------------------------------------------------------
# Detect OS
# ---------------------------------------------------------------------------
OS="$(uname -s)"
case "${OS}" in
    Darwin*) OS_TYPE="mac";;
    Linux*)  OS_TYPE="linux";;
    *)       OS_TYPE="other";;
esac

ARCH="$(uname -m)"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    print_header

    info "OS: ${OS} (${ARCH})"
    echo

    # ------------------------------------------------------------------
    # 1. Package manager (Homebrew on macOS)
    # ------------------------------------------------------------------
    step "1/7  System package manager"

    if [ "$OS_TYPE" = "mac" ]; then
        if command -v brew >/dev/null 2>&1; then
            ok "Homebrew found at $(brew --prefix)"
        else
            warn "Homebrew not found — it's needed to install Python, jq, etc."
            if confirm "Install Homebrew now?"; then
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                # Add brew to PATH for this session (Apple Silicon vs Intel)
                if [ -f "/opt/homebrew/bin/brew" ]; then
                    eval "$(/opt/homebrew/bin/brew shellenv)"
                elif [ -f "/usr/local/bin/brew" ]; then
                    eval "$(/usr/local/bin/brew shellenv)"
                fi
                ok "Homebrew installed"
            else
                err "Homebrew is required on macOS. Aborting."
                exit 1
            fi
        fi
    elif [ "$OS_TYPE" = "linux" ]; then
        if command -v apt-get >/dev/null 2>&1; then
            ok "apt package manager found"
        elif command -v dnf >/dev/null 2>&1; then
            ok "dnf package manager found"
        elif command -v pacman >/dev/null 2>&1; then
            ok "pacman package manager found"
        else
            warn "Could not detect a known package manager — you may need to install dependencies manually"
        fi
    fi

    # ------------------------------------------------------------------
    # 2. Python 3.11+
    # ------------------------------------------------------------------
    step "2/7  Python 3.11+"

    MIN_PY="3.11"
    PYTHON_OK=false

    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            PY_VER=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
            if [ "$(printf '%s\n' "$MIN_PY" "$PY_VER" | sort -V | head -n1)" = "$MIN_PY" ]; then
                ok "Python $PY_VER found at $(which $cmd)"
                PYTHON_CMD="$cmd"
                PYTHON_OK=true
                break
            else
                warn "Python $PY_VER is below the required $MIN_PY"
            fi
        fi
    done

    if [ "$PYTHON_OK" = false ]; then
        warn "Python $MIN_PY+ not found"
        if [ "$OS_TYPE" = "mac" ]; then
            if confirm "Install Python via Homebrew?"; then
                brew install python@3.12
                PYTHON_CMD="python3"
                ok "Python installed"
            else
                err "Python $MIN_PY+ is required. Install it from https://www.python.org/downloads/"
                exit 1
            fi
        elif [ "$OS_TYPE" = "linux" ]; then
            if command -v apt-get >/dev/null 2>&1; then
                warn "Run:  sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv"
            elif command -v dnf >/dev/null 2>&1; then
                warn "Run:  sudo dnf install -y python3.12"
            fi
            err "Please install Python $MIN_PY+ and re-run this script."
            exit 1
        else
            err "Please install Python $MIN_PY+ from https://www.python.org/downloads/"
            exit 1
        fi
    fi

    # ------------------------------------------------------------------
    # 3. uv (Python package manager)
    # ------------------------------------------------------------------
    step "3/7  uv package manager"

    if command -v uv >/dev/null 2>&1; then
        ok "uv found ($(uv --version))"
    else
        warn "uv not found — it's the recommended (and fastest) way to manage Python deps"
        if confirm "Install uv now?"; then
            curl -LsSf https://astral.sh/uv/install.sh | sh
            # Source the env so uv is available in this session
            if [ -f "$HOME/.local/bin/env" ]; then
                source "$HOME/.local/bin/env" 2>/dev/null || true
            fi
            export PATH="$HOME/.local/bin:$PATH"
            if command -v uv >/dev/null 2>&1; then
                ok "uv installed ($(uv --version))"
            else
                err "uv install succeeded but binary not found on PATH."
                err "Try opening a new terminal and re-running this script."
                exit 1
            fi
        else
            err "uv is required — the project uses uv.lock for reproducible installs."
            exit 1
        fi
    fi

    # ------------------------------------------------------------------
    # 4. jq (used by dm-extract.sh and other tools)
    # ------------------------------------------------------------------
    step "4/7  jq (JSON processor)"

    if command -v jq >/dev/null 2>&1; then
        ok "jq found"
    else
        warn "jq not found — some tools (dm-extract.sh) need it"
        if [ "$OS_TYPE" = "mac" ]; then
            if confirm "Install jq via Homebrew?"; then
                brew install jq
                ok "jq installed"
            else
                warn "Skipping jq — some tools may not work correctly"
            fi
        elif [ "$OS_TYPE" = "linux" ]; then
            if command -v apt-get >/dev/null 2>&1; then
                warn "Run:  sudo apt-get install -y jq"
            elif command -v dnf >/dev/null 2>&1; then
                warn "Run:  sudo dnf install -y jq"
            elif command -v pacman >/dev/null 2>&1; then
                warn "Run:  sudo pacman -S jq"
            fi
            warn "Skipping jq — install it manually and re-run if needed"
        fi
    fi

    # ------------------------------------------------------------------
    # 5. Python dependencies (via uv sync)
    # ------------------------------------------------------------------
    step "5/7  Python dependencies"

    # Let the user pick what to install
    EXTRAS_FLAG=""

    if [ "$AUTO_MODE" = true ]; then
        info "Auto mode: installing full dependencies (core + rag + voice)"
        EXTRAS_FLAG="--all-extras"
    else
        echo
        echo "  Select what to install:"
        echo "    1) Core only         — basic DM tools, dice, session management"
        echo "    2) Core + RAG        — adds PDF import & semantic search (recommended)"
        echo "    3) Full              — core + RAG + voice (ElevenLabs TTS)"
        echo "    4) Full + Dev tools  — everything + linting & formatting"
        echo
        echo -n "  Choice [1-4] (default: 2): "
        read -r choice

        case "$choice" in
            1) EXTRAS_FLAG="";;
            3) EXTRAS_FLAG="--all-extras";;
            4) EXTRAS_FLAG="--all-extras";;
            *) EXTRAS_FLAG="--extra rag";;  # default to 2
        esac

        # Dev extras on top if choice 4
        if [ "$choice" = "4" ]; then
            EXTRAS_FLAG="--all-extras"
        fi
    fi

    info "Running: uv sync $EXTRAS_FLAG"
    if [ -n "$EXTRAS_FLAG" ]; then
        uv sync $EXTRAS_FLAG
    else
        uv sync
    fi
    ok "Python dependencies installed"

    # ------------------------------------------------------------------
    # 6. Project setup (env, permissions, world-state dirs)
    # ------------------------------------------------------------------
    step "6/7  Project configuration"

    # .env file
    if [ ! -f ".env" ]; then
        cat > .env << 'ENVEOF'
# DM Claude Configuration
#
# Campaign Settings
DEFAULT_CAMPAIGN_NAME="My Campaign"
DEFAULT_STARTING_LOCATION="Thornwick"

# Optional: Discord webhook for session logging
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ENVEOF
        ok "Created .env file"
    else
        ok ".env file already exists"
    fi

    # World-state directories
    mkdir -p world-state/campaigns
    ok "World-state directories ready"

    # Script permissions (bash scripts only — .py files are invoked via uv run)
    chmod +x tools/*.sh 2>/dev/null || true
    ok "Script permissions set"

    # ------------------------------------------------------------------
    # 7. Verify installation
    # ------------------------------------------------------------------
    step "7/7  Verification"

    PASS=0
    FAIL=0

    # Dice roller
    if uv run python lib/dice.py "1d20" >/dev/null 2>&1; then
        ok "Dice roller works"
        PASS=$((PASS + 1))
    else
        err "Dice roller failed"
        FAIL=$((FAIL + 1))
    fi

    # Anthropic SDK import
    if uv run python -c "import anthropic" 2>/dev/null; then
        ok "Anthropic SDK importable"
        PASS=$((PASS + 1))
    else
        err "Anthropic SDK import failed"
        FAIL=$((FAIL + 1))
    fi

    # Session management
    if bash tools/dm-session.sh status >/dev/null 2>&1; then
        ok "Session management works"
        PASS=$((PASS + 1))
    else
        warn "Session management returned non-zero (may just mean no active campaign yet)"
        PASS=$((PASS + 1))
    fi

    # RAG (if installed)
    if uv run python -c "import chromadb; import sentence_transformers" 2>/dev/null; then
        ok "RAG dependencies available (chromadb + sentence-transformers)"
        PASS=$((PASS + 1))
    else
        info "RAG dependencies not installed (optional — install with: uv sync --extra rag)"
    fi

    # jq
    if command -v jq >/dev/null 2>&1; then
        ok "jq available"
        PASS=$((PASS + 1))
    else
        warn "jq missing — dm-extract.sh will have limited functionality"
    fi

    # Claude Code
    if command -v claude >/dev/null 2>&1; then
        ok "Claude Code CLI found"
        PASS=$((PASS + 1))
    else
        warn "Claude Code CLI not found"
        info "Install it following the instructions on"
        info "https://code.claude.com/docs/en/quickstart#step-1-install-claude-code"
    fi

    # ------------------------------------------------------------------
    # Done!
    # ------------------------------------------------------------------
    echo
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo -e "${BOLD}${BLUE}          Setup Complete!  ($PASS checks passed${FAIL:+, $FAIL failed})${NC}"
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo
    echo "  Quick start:"
    echo "    claude          Launch Claude Code in this project"
    echo "    /new-game       Create a new campaign world"
    echo "    /import          Import a PDF as a campaign"
    echo "    /dm             Start playing!"
    echo
    echo "  Useful commands:"
    echo "    uv run python lib/dice.py \"1d20+5\"     Roll dice"
    echo "    bash tools/dm-search.sh \"query\"         Search world state"
    echo "    bash tools/dm-overview.sh               Campaign overview"
    echo
    if ! command -v claude >/dev/null 2>&1; then
        echo -e "  ${YELLOW}NOTE:${NC} To play, you need Claude Code installed:"
        echo "    npm install -g @anthropic-ai/claude-code"
        echo
    fi
}

main "$@"
