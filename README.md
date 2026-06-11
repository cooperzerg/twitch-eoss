# twitch-eoss

Twitch streaming tools for Valorant.

## Projects

### sound-skins-quiz

Valorant weapon skin sound quiz for Twitch streaming. Hear a weapon firing sound, guess which skin collection it belongs to.

```bash
cd sound-skins-quiz

# Web overlay (for OBS + Streamer.bot)
pip install flask
python server.py

# Standalone pygame version
pip install pygame
python guess.py
```

## Structure

```
twitch-eoss/
├── sound-skins-quiz/   # Skin sound quiz
│   ├── server.py       # Flask API server
│   ├── guess.py        # pygame GUI
│   ├── an.py           # Mapping generator
│   ├── collection_mapping.json
│   ├── static/         # OBS overlay (1200x700)
│   ├── img/            # Skin images (.webp)
│   └── sfx/            # Weapon sounds (.mp3)
├── bot/                # Twitch chat bot (planned)
└── scripts/            # OBS scripts (planned)
```
