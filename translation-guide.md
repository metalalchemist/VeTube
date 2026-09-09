# Translation Guide

**Help make VeTube accessible worldwide** — VeTube uses gettext for internationalization. This guide explains how to translate the application into new languages or improve existing translations.

## Quick Path

1. **Choose your language** — Check if translation exists in `locales/[lang]/LC_MESSAGES/VeTube.po`
2. **Edit the .po file** — Use a PO editor or text editor
3. **Translate strings** — Fill in `msgstr` for each `msgid`
4. **Compile to .mo** — Run `uv run python -m babel.messages.frontend compile`
5. **Test** — Launch VeTube and verify your translations
6. **Submit PR** — Create a pull request with your changes

## Current Languages

| Language | Code | Status | Maintainer |
|----------|------|--------|------------|
| Czech | `cs` | Active | 4Sense Gaming |
| English | `en` | Active | Community |
| French | `fr` | Active | Community |
| Indonesian | `id` | Active | Community |
| Polish | `pl` | Active | Community |
| Portuguese | `pt` | Active | Community |
| Russian | `ru` | Active | Kostenkov-2021 |
| Spanish | `es` | Base language | — |

**Missing your language?** See [Adding a New Language](#adding-a-new-language) below.

## How Translations Work

VeTube uses the **gettext** system for internationalization:

- **Source language**: Spanish (all `msgid` strings are in Spanish)
- **Translation files**: `locales/[lang]/LC_MESSAGES/VeTube.po`
- **Compiled files**: `locales/[lang]/LC_MESSAGES/VeTube.mo` (binary, used at runtime)

### File Structure

```
locales/
├── cs/
│   └── LC_MESSAGES/
│       ├── VeTube.po  ← Edit this file
│       └── VeTube.mo  ← Compiled (auto-generated)
├── en/
│   └── LC_MESSAGES/
│       ├── VeTube.po
│       └── VeTube.mo
└── [other languages...]
```

### PO File Format

Each translatable string has this format:

```po
#: source_file.py:line_number
msgid "Original text in Spanish"
msgstr "Translated text in your language"
```

**Example:**

```po
#: run_main_window.py:32
msgid "VeTube ya se encuentra en ejecución. Cierra la otra instancia antes de iniciar esta."
msgstr "VeTube is already running. Close the other instance before starting this one."
```

## Translating Existing Languages

### Using a PO Editor (Recommended)

PO editors provide a user-friendly interface for translations:

**Recommended tools:**
- **[Poedit](https://poedit.net/)** — Cross-platform, free, easy to use
- **[Lokalize](https://apps.kde.org/lokalize/)** — KDE's translation tool
- **[VS Code with gettext extension](https://marketplace.visualstudio.com/items?itemName=mrorz.language-gettext)** — If you prefer VS Code

**Steps with Poedit:**

1. **Open Poedit**
2. **File → Open** → Select `locales/[lang]/LC_MESSAGES/VeTube.po`
3. **Translate each string** — Poedit shows original and translation side-by-side
4. **Save** — Poedit automatically compiles the `.mo` file
5. **Test** — Launch VeTube to verify

### Using a Text Editor

If you prefer editing directly:

1. **Open the .po file** in your favorite text editor
2. **Find untranslated strings** — Look for empty `msgstr ""`
3. **Add your translation** inside the quotes
4. **Save the file**

**Example:**

```po
#: controller/main_controller.py:123
msgid "Conectar"
msgstr ""  ← Add translation here
```

Becomes:

```po
#: controller/main_controller.py:123
msgid "Conectar"
msgstr "Connect"
```

### Compiling Translations

After editing `.po` files, compile them to `.mo`:

```powershell
# Compile all languages
uv run python -m babel.messages.frontend compile -d locales

# Compile specific language
uv run python -m babel.messages.frontend compile -l en -d locales
```

The compiled `.mo` files are what VeTube actually uses at runtime.

## Testing Your Translations

### Quick Test

1. **Compile** your `.po` file to `.mo`
2. **Launch VeTube**: `uv run python run_main_window.py`
3. **Change language** in Settings → Interface
4. **Navigate the app** and verify your translations appear correctly

### Testing Compiled App

To test in the compiled executable:

1. **Rebuild**: `uv run cxfreeze build`
2. **Run**: `build\exe.win-amd64-3.14\VeTube.exe`
3. **Verify** translations appear correctly

## Translation Guidelines

### General Principles

**DO:**
- ✅ Keep translations natural and idiomatic
- ✅ Maintain the same meaning as the original
- ✅ Respect UI space constraints (some strings appear in buttons)
- ✅ Test translations in context
- ✅ Use consistent terminology throughout

**DON'T:**
- ❌ Translate variable names or code
- ❌ Translate technical terms that are commonly kept in English (e.g., "TTS", "URL")
- ❌ Add extra formatting or line breaks not present in original
- ❌ Leave strings untranslated if you can help it

### Handling Variables

Some strings contain variables marked with `{}` or `%s`:

```po
msgid "Error al conectar con {platform}"
msgstr "Error connecting to {platform}"
```

**Rules:**
- **Keep variable placeholders** exactly as they appear
- **You can reorder** variables if needed for your language's grammar
- **Never translate** the variable name itself

### Plural Forms

Some languages have complex plural rules. The `.po` header defines plural forms:

```po
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
```

For plural strings:

```po
msgid "1 mensaje"
msgid_plural "{count} mensajes"
msgstr[0] "1 message"
msgstr[1] "{count} messages"
```

### Context Comments

Some strings have context comments to help translation:

```po
#. Button label for connecting to chat
msgid "Conectar"
msgstr "Connect"
```

Read these comments for guidance on how the string is used.

## Adding a New Language

### Step 1: Create Language Directory

```powershell
# Replace 'xx' with your language code (e.g., 'de' for German)
New-Item -ItemType Directory -Path "locales\xx\LC_MESSAGES" -Force
```

### Step 2: Extract Translatable Strings

Generate a template `.pot` file:

```powershell
uv run python -m babel.messages.frontend extract -o locales/VeTube.pot .
```

### Step 3: Create PO File

Copy the template to your language:

```powershell
Copy-Item locales\VeTube.pot locales\xx\LC_MESSAGES\VeTube.po
```

### Step 4: Update PO Header

Edit the header in your new `.po` file:

```po
msgid ""
msgstr ""
"Project-Id-Version: VeTube 3.94\n"
"Report-Msgid-Bugs-To: https://github.com/metalalchemist/VeTube/issues\n"
"POT-Creation-Date: 2026-07-07 21:03-0700\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: YOUR NAME <your.email@example.com>\n"
"Language-Team: YOUR LANGUAGE <LL@li.org>\n"
"Language: xx\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
```

**Important fields:**
- `Language`: Your language code
- `Last-Translator`: Your name and email
- `Plural-Forms`: Correct plural rules for your language

### Step 5: Translate

Open the `.po` file and translate all strings. See [Translating Existing Languages](#translating-existing-languages) above.

### Step 6: Compile and Test

```powershell
# Compile your language
uv run python -m babel.messages.frontend compile -l xx -d locales

# Test
uv run python run_main_window.py
```

### Step 7: Update languageHandler.py

Add your language to the language list in `utils/languageHandler.py`:

```python
def getAvailableLanguages():
    # Add your language code to this list
    languages = ["en", "fr", "pt", "pl", "cs", "id", "xx"]
    # ...
```

### Step 8: Submit PR

Create a pull request with:
- Your new `locales/xx/LC_MESSAGES/VeTube.po` file
- The compiled `VeTube.mo` file
- Any changes to `languageHandler.py`

## Updating Translations

When new strings are added to VeTube, existing translations need updates.

### Step 1: Update POT Template

```powershell
uv run python -m babel.messages.frontend extract -o locales/VeTube.pot .
```

### Step 2: Merge with Existing PO

```powershell
uv run python -m babel.messages.frontend update -i locales/VeTube.pot -o locales/en/LC_MESSAGES/VeTube.po
```

This adds new strings and marks obsolete ones.

### Step 3: Translate New Strings

Open the `.po` file and look for:
- **Fuzzy translations** (marked with `#, fuzzy`) — Review and update
- **Untranslated strings** (empty `msgstr`) — Add translations
- **Obsolete strings** (marked with `#~`) — Can be removed

### Step 4: Compile and Test

```powershell
uv run python -m babel.messages.frontend compile -d locales
```

## Common Translation Issues

### String Not Appearing in Translation

**Problem:** You translated a string but it still shows in Spanish.

**Solutions:**
1. **Did you compile?** — Run `uv run python -m babel.messages.frontend compile -d locales`
2. **Check language setting** — Ensure VeTube is using your language
3. **Restart VeTube** — Translations are loaded at startup
4. **Check for typos** — Ensure `msgid` matches exactly (including spaces)

### Fuzzy Translations

**Problem:** Poedit marks translations as "fuzzy".

**Solution:** Fuzzy means the original string changed slightly. Review the translation and remove the `#, fuzzy` marker:

```po
#, fuzzy  ← Remove this line after reviewing
msgid "Original text"
msgstr "Your translation"
```

### Encoding Issues

**Problem:** Special characters (accents, non-Latin scripts) appear garbled.

**Solution:** Ensure your `.po` file is saved as UTF-8:
- **Poedit**: Automatically handles encoding
- **Text editor**: Save with UTF-8 encoding (no BOM)

## Translation Tools Comparison

| Tool | Platform | Pros | Cons |
|------|----------|------|------|
| **Poedit** | Windows, Mac, Linux | User-friendly, auto-compiles | Requires installation |
| **Lokalize** | Linux, Windows | Powerful, KDE integration | Less intuitive for beginners |
| **VS Code + gettext** | Cross-platform | Integrated with code, syntax highlighting | Manual compilation |
| **Text editor** | Any | Simple, no dependencies | Error-prone, manual work |

**Recommendation:** Use **Poedit** for most users. It handles compilation automatically and provides a clear interface.

## Translation Workflow Summary

```
1. Extract strings    → uv run python -m babel.messages.frontend extract
2. Update PO files    → uv run python -m babel.messages.frontend update
3. Translate          → Edit .po files with Poedit or text editor
4. Compile            → uv run python -m babel.messages.frontend compile
5. Test               → Launch VeTube and verify
6. Submit PR          → Create pull request on GitHub
```

## Resources

### Documentation
- **[gettext Manual](https://www.gnu.org/software/gettext/manual/)** — Complete gettext documentation
- **[Babel Documentation](https://babel.pocoo.org/)** — Python internationalization library
- **[Poedit Manual](https://poedit.net/wiki)** — Poedit user guide

### Tools
- **[Poedit](https://poedit.net/)** — Recommended PO editor
- **[Lokalize](https://apps.kde.org/lokalize/)** — KDE translation tool
- **[VS Code gettext extension](https://marketplace.visualstudio.com/items?itemName=mrorz.language-gettext)** — Syntax highlighting

### Community
- **[GitHub Discussions](https://github.com/metalalchemist/VeTube/discussions)** — Ask translation questions
- **[GitHub Issues](https://github.com/metalalchemist/VeTube/issues)** — Report translation bugs

## FAQ

**Q: Do I need to know programming to translate?**
A: No! You only need to understand the source language (Spanish or English) and your target language. PO editors make it easy.

**Q: What if I don't know how to translate a technical term?**
A: Keep it in English or ask in [GitHub Discussions](https://github.com/metalalchemist/VeTube/discussions). Some terms like "TTS", "URL", "API" are commonly kept in English.

**Q: Can I translate incrementally?**
A: Yes! You don't need to translate everything at once. Untranslated strings fall back to the original Spanish.

**Q: How do I test my translations without compiling the whole app?**
A: Run VeTube in development mode: `uv run python run_main_window.py`. Changes to `.mo` files are picked up on restart.

**Q: What if my language has regional variants (e.g., Portuguese vs Brazilian Portuguese)?**
A: Use language codes with regions: `pt_BR` for Brazilian Portuguese, `pt_PT` for European Portuguese. Create separate directories for each.

**Q: Can I suggest improvements to existing translations?**
A: Absolutely! Submit a PR with your improvements. Translation quality is a community effort.

---

**Thank you for helping make VeTube accessible to more people!** 🌍

Questions? Ask in [GitHub Discussions](https://github.com/metalalchemist/VeTube/discussions).
