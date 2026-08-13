# Contributing to GM Claude

Thank you for your interest in contributing to GM Claude! This guide will help you get started with contributing to the project.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to make D&D more fun and accessible!

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in [GitHub Issues](https://github.com/Sstobo/Claude-Code-Game-Master/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (if it's a bug)
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)

### Suggesting Features

1. Open a [Discussion](https://github.com/Sstobo/Claude-Code-Game-Master/discussions) first
2. Describe the feature and why it would be useful
3. Consider how it fits with the project's goals

### Contributing Code

#### Setup Development Environment

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/Sstobo/Claude-Code-Game-Master.git
cd Claude-Code-Game-Master
```

3. Install with development dependencies:
```bash
./install.sh
# Choose option 5 (Development)
```

4. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

#### Development Guidelines

##### Python Code

- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small
- Write tests for new features

Run code formatters before committing:
```bash
black .
ruff check . --fix
```

##### Bash Scripts

- Follow the existing pattern in `tools/common.sh`
- Use the common utility functions
- Add proper error handling
- Include usage examples in comments
- Make scripts composable, not customizable

##### Testing

Run tests before submitting (pytest is in the `dev` extra):
```bash
uv pip install pytest   # first time
uv run pytest
```

Tests are hermetic: they copy the Dungeon Crawler Carl golden fixture
(`tests/fixtures/world-state/`) into a tmp dir, so they never touch a live
campaign. Add new tests for your features in the `tests/` directory.

#### Commit Messages

Use clear, descriptive commit messages:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks

Examples:
```
feat: add support for multi-class characters
fix: correct dice roll parsing for complex expressions
docs: update README with new voice commands
```

#### Pull Request Process

1. Update documentation for any new features
2. Add tests for new functionality
3. Ensure all tests pass
4. Update the README.md if needed
5. Submit a pull request with:
   - Clear title and description
   - Link to any related issues
   - Screenshots/examples if applicable

### Adding New Tools

To add a new GM tool:

1. Create the script in `tools/gm-yourfeature.sh`
2. Source `common.sh` for utilities
3. Follow the existing pattern:
   - Argument parsing
   - Input validation
   - JSON manipulation via Python
   - Status output using common functions

Example template:
```bash
#!/bin/bash
# gm-yourfeature.sh - Description

# Source common utilities
source "$(dirname "$0")/common.sh"

# Usage check
if [ "$#" -lt 1 ]; then
    echo "Usage: gm-yourfeature.sh <action> [args]"
    exit 1
fi

ACTION="$1"

case "$ACTION" in
    add)
        # Implementation
        success "Feature added"
        ;;
    *)
        error "Unknown action: $ACTION"
        exit 1
        ;;
esac
```

### Adding Claude Agents

To add a new Claude agent:

1. Create `.claude/agents/your-agent.md`
2. Define the agent's:
   - Purpose and triggers
   - Required tools
   - Workflow steps
   - Example interactions

### Documentation

The docs under `docs/` are an [OKF](docs/log.md) knowledge bundle: every doc's
frontmatter declares the source files whose change would make it wrong, and drift is
machine-checked against git.

- Before editing code, ask which docs claim it:
  `node ~/.claude/skills/okf/scripts/okf.mjs status <files…>` (settled flags live in
  `docs/log.md`)
- Update the claiming docs **in the same commit** as the code
- Docs hold what the code cannot state (the why, cross-file invariants, landmines) —
  a doc that restates code gets deleted, not maintained
- Added or moved docs → rerun `okf.mjs index docs`
- Keep the README.md up to date

## Project Structure

Understanding the project structure helps with contributions:

- `tools/` - Core bash scripts for GM operations
- `lib/` - Python utility libraries
- `features/` - D&D 5e specific features
- `world-state/` - Campaign data storage
- `.claude/` - Claude Code configuration
- `tests/` - Test suite

## Getting Help

- Join our [Discord](https://discord.gg/dmclaude)
- Ask questions in [Discussions](https://github.com/Sstobo/Claude-Code-Game-Master/discussions)
- Check the [Wiki](https://github.com/Sstobo/Claude-Code-Game-Master/wiki)

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- Our Discord server

Thank you for helping make GM Claude better for everyone!