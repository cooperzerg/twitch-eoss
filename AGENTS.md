# twitch-eoss

Twitch streaming tools for Valorant.

## Projects

### sound-skins-quiz

Valorant weapon skin sound quiz for Twitch streaming. Hear a weapon firing sound, guess which skin collection it belongs to.

## Quick Start

```bash
cd sound-skins-quiz

# Web overlay (for Streamer.bot + OBS)
pip install flask
python server.py
# Open http://localhost:8081 in browser
# OBS Browser Source: http://localhost:8081 (1200x700)

# Standalone pygame version
pip install pygame
python guess.py
```

## API Endpoints

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/next_round` | POST | — | Start round, returns question |
| `/vote` | POST | `{"answer":"A"}` | Submit vote from Streamer.bot |
| `/vote/chat` | POST | `{"char":"a"}` | Chat vote (A/B/C/D) |
| `/vote/result` | GET | — | Current vote result |
| `/state` | GET | — | Current state (for overlay polling) |
| `/reset` | POST | — | Reset score |
| `/health` | GET | — | Health check |

## Chat Vote Mapping

| Option | Keys (EN + RU, case-insensitive) |
|--------|-----------------------------------|
| A | A a А а |
| B | B b Б б |
| C | C c Ц ц С с |
| D | D d Д д |

## Streamer.bot Integration

### Triggers
- Overwolf (Fired Shots) → 3+ kills → Streamer.bot
- Channel Points redemption "Квиз"
- `!quiz` command with cooldown

### Flow
```
Trigger → Streamer.bot → POST /next_round → server
         → OBS Browser Source shows overlay
         → Chat votes A/B/C/D (15 sec timer)
         → Streamer.bot counts votes → POST /vote
         → Overlay shows result
```

### OBS Settings
- Browser Source: `http://<server_ip>:8081`
- Resolution: 1200x700
- Custom CSS: leave empty
- Audio: Monitor Off (streamer doesn't hear quiz sounds)
- Game audio ducked ~-15dB during quiz

## Architecture

- **guess.py** — pygame GUI (standalone)
- **server.py** — Flask API server
- **static/index.html** — overlay (1200x700, transparent bg)
- **collection_mapping.json** — 65 collections, 140 skins
- **sfx/** — weapon sounds (.mp3)
- **img/** — skin images (.webp)
- **an.py** — utility to regenerate collection_mapping.json from img/sfx folders

## Rules
- 1 question per trigger (not multi-question blocks)
- 15 second voting timer
- Preserve image aspect ratio (never force square)
- pygame: load sound once per question (boolean flag)
- Server runs on Android phone or Windows PC (~20 MB RAM)

---

## Streamer.bot

Portable installation in `streamerbot/`.

### OBS Connection
- Host: `127.0.0.1:4455`
- Password: `J4XQL1fFLDmXeODI`

### Actions
| Group | Action | Description |
|-------|--------|-------------|
| Cluthes | clutch_vote | Голосование за клатчи |
| [Currency] Core System | — | Система валюты/очков |
| Torunaments | — | Турниры |
| Утилиты | — | Разные утилиты |

### Commands
| Command | Description |
|---------|-------------|
| `!quiz` | Запустить квиз (planned) |
| `!top` | Клатч предикторы |
| `!points` | Показать очки |
| `!lose` / `!l` / `!невин` | Клатч проигрыш |

### Running
```bash
cd streamerbot
./Streamer.bot.exe
```
