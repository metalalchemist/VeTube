# VeTube

**Read live chat messages aloud from multiple streaming platforms** — VeTube brings accessibility to live streaming by converting chat messages to speech in real-time.

![Version](https://img.shields.io/badge/version-3.94-blue)
![Python](https://img.shields.io/badge/python-3.14+-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

## What is VeTube?

VeTube is a Windows desktop application that monitors live chat from streaming platforms and reads messages aloud using text-to-speech. Perfect for streamers who want to stay engaged with their chat while focused on gameplay, or for accessibility needs.

## Features

- **Multi-platform support**: YouTube, Twitch, TikTok, Kick, Discord, and "La sala de juegos"
- **Multiple TTS engines**: Piper (high-quality neural voices), Windows OneCore, SAPI5
- **Real-time chat monitoring**: Instant message detection and voice synthesis
- **Multi-language interface**: Available in Spanish, English, French, Portuguese, Polish, Czech, Indonesian, and Russian
- **Customizable audio**: Sound effects, volume control, voice selection
- **Chat statistics**: Track messages, members, donations, and more
- **Message archiving**: Save and review important messages
- **Favorites management**: Quick access to your favorite streams

## Installation

### Option 1: Scoop (Recommended)

```powershell
# Add the Scoop bucket
scoop bucket add row https://github.com/Row0902/scoop-bucket

# Install VeTube
scoop install vetube
```

### Option 2: Download Installer

Download the latest MSI installer from the [Releases page](https://github.com/metalalchemist/VeTube/releases).

### Option 3: Build from Source

```powershell
# Clone the repository
git clone https://github.com/metalalchemist/VeTube.git
cd VeTube

# Install dependencies with uv
uv sync

# Run the application
uv run python run_main_window.py

# Or build executable
uv run cxfreeze build
```

## Package Manager Support

We're actively working on making VeTube available through additional package managers:

- [x] **Scoop** - Available now via [Row0902/scoop-bucket](https://github.com/Row0902/scoop-bucket)
- [ ] **Winget** - In progress
- [ ] **Chocolatey** - In progress

## Quick Start

1. **Launch VeTube** from Start Menu or desktop shortcut
2. **Select platform** from the dropdown (YouTube, Twitch, TikTok, Kick, Discord, or La sala de juegos)
3. **Enter channel URL or username** in the text field
4. **Press Enter** or click "Connect" to start monitoring chat
5. **Listen** as messages are read aloud in real-time

### Example URLs by Platform

| Platform | Example |
|----------|---------|
| YouTube | `https://www.youtube.com/@channel/live` or just `@channel` |
| Twitch | `https://www.twitch.tv/channel` or just `channel` |
| TikTok | `https://www.tiktok.com/@username/live` or `@username` |
| Kick | `https://www.kick.com/channel` or just `channel` |
| Discord | Paste text channel URL (requires token in settings) |
| La sala de juegos | Leave empty and press Enter |

## Documentation

- **[User Guide](user-guide.md)** — Complete guide to all features and settings
- **[Translation Guide](translation-guide.md)** — How to translate VeTube to your language
- **[Contributing](contributing.md)** — How to contribute to VeTube development
- **[Contributors](contributors.md)** — List of amazing people who contributed to VeTube
- **[Release Notes](release-notes.md)** — Changelog and version history

## Translations

VeTube is available in multiple languages. See the **[Translation Guide](translation-guide.md)** if you want to contribute translations.

- [Čeština (Czech)](doc/cs/readme.md)
- [English](doc/en/readme.md)
- [Español (Spanish)](doc/es/readme.md)
- [Français (French)](doc/fr/readme.md)
- [Bahasa Indonesia (Indonesian)](doc/id/readme.md)
- [Polski (Polish)](doc/pl/readme.md)
- [Português (Portuguese)](doc/pt/readme.md)
- [Русский (Russian)](doc/ru/readme.md)

## Requirements

- **OS**: Windows 10 or later
- **Python**: 3.14+ (for building from source)
- **Dependencies**: Automatically installed via Scoop or included in MSI installer

## Technology Stack

- **GUI**: wxPython
- **TTS**: Piper, Windows OneCore, SAPI5
- **Audio**: BASS library
- **Chat protocols**: chat-downloader, pytchat, kick.py, TikTokLive, discord.py
- **Build system**: cx_Freeze
- **Package manager**: uv

## Support

- **Issues**: [GitHub Issues](https://github.com/metalalchemist/VeTube/issues)
- **Discussions**: [GitHub Discussions](https://github.com/metalalchemist/VeTube/discussions)

## License

This project is licensed under the GPL-3.0 License — see the [LICENSE](LICENSE) file for details.

## Credits

VeTube is developed and maintained by [Cesar Verastegui](https://github.com/metalalchemist) and [Rowell Urbaez Reyes](https://github.com/Row0902), with contributions from the community.

Special thanks to:
- The [Piper TTS](https://github.com/rhasspy/piper) project for high-quality neural voices
- The [BASS](https://www.un4seen.com/) audio library team
- All [contributors](contributors.md) who have helped make VeTube better

---

**Made with ❤️ for the streaming community**
