# Contributing to VeTube

**Help make live streaming more accessible** — VeTube thrives on community contributions. Whether you're fixing bugs, adding features, improving translations, or enhancing documentation, your help is welcome.

## Quick Path

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** for your changes (`git checkout -b feature/your-feature`)
4. **Make changes** following our conventions
5. **Test** your changes
6. **Commit** with clear messages (`git commit -m "feat: add your feature"`)
7. **Push** to your fork (`git push origin feature/your-feature`)
8. **Open a Pull Request** from your fork to `main`

## Development Setup

### Prerequisites

- **Windows 10+** (VeTube is Windows-only)
- **Python 3.14+**
- **uv** (Python package manager)
- **Git**

### Installation

```powershell
# Clone your fork
git clone https://github.com/YOUR_USERNAME/VeTube.git
cd VeTube

# Install dependencies
uv sync

# Run the application
uv run python run_main_window.py

# Build executable (optional)
uv run cxfreeze build
```

> **`requirements.txt`**: kept only for contributors on a plain `venv` + `pip`
> setup. It is generated automatically from `uv.lock` on every release — do
> **not** edit it by hand. `pyproject.toml` + `uv.lock` are the source of truth.

### Project Structure

```
VeTube/
├── controller/          # MVC controllers
├── ui/                  # wxPython GUI components
├── servicios/           # Chat platform services (YouTube, Twitch, etc.)
├── utils/               # Utility functions
├── globals/             # Global state and configuration
├── TTS/                 # Text-to-speech engines
├── players/             # Audio playback
├── helpers/             # Helper functions
├── locales/             # Translation files (.mo)
├── sounds/              # Sound effects
├── 64/                  # External binaries (bypass, VLC, Sonata)
├── doc/                 # Documentation translations
├── run_main_window.py   # Application entry point
└── pyproject.toml       # Project configuration
```

## Code Conventions

### Python Style

- **Follow PEP 8** with these specifics:
  - Use 4 spaces for indentation
  - Maximum line length: 100 characters
  - Use `snake_case` for variables and functions
  - Use `PascalCase` for classes
  - Use `UPPER_CASE` for constants

- **Imports**: Group in this order:
  1. Standard library
  2. Third-party packages
  3. Local application imports

```python
# Good
import os
import sys
from pathlib import Path

import wx
import httpx

from globals.paths import BASE_DIR
from utils.languageHandler import getAvailableLanguages
```

### File Paths

**Always use absolute paths** via `globals/paths.py` for resources:

```python
# ✅ Good
from globals.paths import DATA_FILE, LOCALES_DIR, SOUNDS_DIR

config_path = DATA_FILE
locales_path = LOCALES_DIR

# ❌ Bad - breaks in compiled app
config_path = "data.json"
locales_path = "locales"
```

### wxPython GUI

- Keep UI logic in `ui/` directory
- Controllers in `controller/` directory
- Use wx sizers for layout (never absolute positioning)
- Test with screen readers for accessibility

### Services Architecture

Each chat platform is a separate service in `servicios/`:

```python
# Pattern for new services
class ServicioPlataforma:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.plataforma = plataforma
        self.chat_controller = chat_controller
        self.is_running = False

    def start(self):
        """Start monitoring chat"""
        pass

    def stop(self):
        """Stop monitoring chat"""
        pass
```

## Testing

### Manual Testing

Since VeTube lacks automated tests, manual testing is critical:

1. **Test in development**: `uv run python run_main_window.py`
2. **Test compiled build**: `uv run cxfreeze build` then run `VeTube.exe`
3. **Test each platform** you modified
4. **Test with screen reader** enabled
5. **Test error cases** (invalid URLs, network issues, etc.)

### Testing Checklist

Before submitting a PR:

- [ ] App runs without errors in development mode
- [ ] App runs without errors when compiled
- [ ] Modified features work as expected
- [ ] No regressions in existing features
- [ ] Error messages are clear and translated
- [ ] Logs don't show new warnings

## Pull Request Process

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for new platform
fix: resolve crash when disconnecting
docs: update installation instructions
refactor: simplify service initialization
test: add manual test cases for Twitch
chore: update dependencies
```

### PR Description Template

```markdown
## What does this PR do?

[Brief description of changes]

## Why is this needed?

[Problem this solves or feature this adds]

## How to test

1. [Step 1]
2. [Step 2]
3. [Expected result]

## Checklist

- [ ] Code follows project conventions
- [ ] Tested in development mode
- [ ] Tested compiled build
- [ ] No new warnings in logs
- [ ] Documentation updated (if needed)
- [ ] Translations updated (if needed)

## Screenshots

[If UI changes, add before/after screenshots]
```

### Review Process

1. **Automated checks** run on PR creation
2. **Maintainer review** within 3-5 days
3. **Address feedback** and push updates
4. **Merge** after approval

## Reporting Bugs

### Before Reporting

- Search [existing issues](https://github.com/metalalchemist/VeTube/issues)
- Check if bug exists in latest version
- Gather information (logs, steps to reproduce)

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Logs**
```
Paste relevant log entries from logs/vetube.log
```

**Environment:**
- OS: [e.g., Windows 11]
- VeTube version: [e.g., 3.94]
- Installation method: [e.g., Scoop, MSI]

**Additional context**
Any other context about the problem.
```

## Suggesting Features

### Before Suggesting

- Check [existing issues](https://github.com/metalalchemist/VeTube/issues) for similar requests
- Consider if feature aligns with project goals
- Think about implementation complexity

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Mockups, examples, or references.
```

## Translation Contributions

VeTube supports multiple languages. To contribute translations:

1. **Read the [Translation Guide](translation-guide.md)** — Complete guide to the translation process
2. **Locate translation files** in `locales/[lang]/LC_MESSAGES/VeTube.po`
3. **Use a PO editor** like [Poedit](https://poedit.net/) or VS Code extensions
4. **Translate strings** maintaining context
5. **Compile and test** with the application
6. **Submit PR** with your changes

### Translation Guidelines

- Maintain consistent terminology
- Respect UI space constraints
- Test with actual application
- Include cultural context when needed
- Follow the detailed guidelines in the [Translation Guide](translation-guide.md)

## Code of Conduct

### Our Pledge

We are committed to making participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior:**
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Report unacceptable behavior to the project maintainers. All complaints will be reviewed and investigated promptly.

## Getting Help

- **Documentation**: [User Guide](user-guide.md)
- **Questions**: [GitHub Discussions](https://github.com/metalalchemist/VeTube/discussions)
- **Issues**: [GitHub Issues](https://github.com/metalalchemist/VeTube/issues)

## Recognition

All contributors are listed in [contributors.md](contributors.md). Your contributions are valued and appreciated!

---

**Thank you for contributing to VeTube!** 🎉
