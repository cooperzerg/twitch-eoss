#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
from pathlib import Path
from collections import defaultdict
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
MAPPING_FILE = ROOT / "collection_mapping.json"
SFX_DIR = ROOT / "sfx"
IMG_DIR = ROOT / "img"
ROUNDS = 1

app = Flask(__name__, static_folder="static")

collections = []
all_skins = []
questions = []
current_question = None
current_options = []
state = "idle"
score = 0
total_played = 0
vote_map = {"A": 0, "B": 0, "C": 0, "D": 0}
voters = {"A": [], "B": [], "C": [], "D": []}
quiz_round = 0
quiz_total = 0

CHAR_MAP = {
    "a": "A", "A": "A", "а": "A", "А": "A",
    "b": "B", "B": "B", "б": "B", "Б": "B",
    "c": "C", "C": "C", "ц": "C", "Ц": "C", "с": "C", "С": "C",
    "d": "D", "D": "D", "д": "D", "Д": "D",
}


def load_data():
    global collections, all_skins, questions
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    collections = []
    for col in raw:
        sfx = Path(col["sfx"]) if col.get("sfx") else None
        if sfx and sfx.exists() and col.get("skins"):
            valid_skins = [s for s in col["skins"] if Path(s["image"]).exists()]
            if valid_skins:
                collections.append({
                    "collection": col["collection"],
                    "sfx": str(sfx),
                    "skins": valid_skins,
                })

    all_skins = []
    for col in collections:
        for skin in col["skins"]:
            all_skins.append({
                "collection": col["collection"],
                "weapon": skin["weapon"],
                "image": skin["image"],
                "sfx": col["sfx"],
            })


def generate_question():
    if not all_skins:
        return None

    col = random.choice(collections)
    correct = random.choice(col["skins"])
    weapon = correct["weapon"]

    by_weapon = defaultdict(list)
    for s in all_skins:
        if s["weapon"] == weapon and s["collection"] != col["collection"]:
            by_weapon[s["weapon"]].append(s)

    candidates = list(by_weapon.get(weapon, []))
    if len(candidates) < 3:
        others = [s for s in all_skins if s["collection"] != col["collection"]]
        candidates += others
    if len(candidates) < 3:
        return None

    distractors = random.sample(candidates, 3)
    options = distractors + [{
        "collection": col["collection"],
        "weapon": weapon,
        "image": correct["image"],
        "sfx": col["sfx"],
    }]
    random.shuffle(options)

    labels = ["A", "B", "C", "D"]
    for i, opt in enumerate(options):
        opt["label"] = labels[i]
        opt["image_url"] = f"/img/{Path(opt['image']).name}"

    return {
        "collection": col["collection"],
        "weapon": weapon,
        "sfx_url": f"/sfx/{Path(col['sfx']).name}",
        "options": options,
    }


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


@app.route("/sfx/<path:name>")
def serve_sfx(name):
    return send_from_directory(str(SFX_DIR), name)


@app.route("/img/<path:name>")
def serve_img(name):
    return send_from_directory(str(IMG_DIR), name)


@app.route("/next_round", methods=["POST"])
def next_round():
    global current_question, current_options, state, vote_map, voters, quiz_round, quiz_total, score, total_played
    data = request.get_json(force=True, silent=True) or {}

    if state == "idle":
        quiz_total = data.get("questions", 1)
        quiz_round = 0
        score = 0
        total_played = 0

    if quiz_round >= quiz_total and quiz_total > 0:
        state = "idle"
        return jsonify({"error": "quiz finished", "score": score, "total": total_played})

    q = generate_question()
    if not q:
        return jsonify({"error": "no questions available"}), 500

    current_question = q
    current_options = q["options"]
    state = "playing"
    vote_map = {"A": 0, "B": 0, "C": 0, "D": 0}
    voters = {"A": [], "B": [], "C": [], "D": []}
    quiz_round += 1

    return jsonify({
        "round": quiz_round,
        "total": quiz_total,
        "weapon": q["weapon"],
        "sfx_url": q["sfx_url"],
        "options": [{"label": o["label"], "collection": o["collection"], "image_url": o["image_url"]} for o in q["options"]],
    })


@app.route("/vote", methods=["POST"])
def vote():
    global state, score, total_played
    data = request.get_json(force=True)
    answer = data.get("answer", "").upper()
    correct_label = ""
    for opt in current_options:
        if opt["collection"] == current_question["collection"]:
            correct_label = opt["label"]
            break

    is_correct = answer == correct_label
    if is_correct:
        score += 1
    total_played += 1
    state = "feedback"

    return jsonify({
        "correct": is_correct,
        "correct_label": correct_label,
        "correct_collection": current_question["collection"],
        "weapon": current_question["weapon"],
        "score": score,
        "total": total_played,
    })


@app.route("/state", methods=["GET"])
def get_state():
    resp = {"state": state, "score": score, "total": total_played, "round": quiz_round, "total_rounds": quiz_total}
    if state == "playing" and current_question:
        resp["weapon"] = current_question["weapon"]
        resp["sfx_url"] = current_question["sfx_url"]
        resp["options"] = [{"label": o["label"], "collection": o["collection"], "image_url": o["image_url"]} for o in current_options]
    elif state == "feedback" and current_question:
        resp["weapon"] = current_question["weapon"]
        resp["correct_collection"] = current_question["collection"]
        resp["correct_label"] = next((o["label"] for o in current_options if o["collection"] == current_question["collection"]), "")
        resp["options"] = [{"label": o["label"], "collection": o["collection"], "image_url": o["image_url"]} for o in current_options]
        resp["correct_voters"] = voters.get(resp["correct_label"], [])
    return jsonify(resp)


@app.route("/reset", methods=["POST"])
def reset():
    global state, score, total_played, current_question, quiz_round, quiz_total
    state = "idle"
    score = 0
    total_played = 0
    current_question = None
    quiz_round = 0
    quiz_total = 0
    return jsonify({"ok": True})


@app.route("/vote/chat", methods=["POST"])
def vote_chat():
    global vote_map, voters
    data = request.get_json(force=True)
    char = data.get("char", "")
    username = data.get("username", "anonymous")
    mapped = CHAR_MAP.get(char, "")
    if mapped in vote_map:
        vote_map[mapped] += 1
        if username not in voters[mapped]:
            voters[mapped].append(username)
    return jsonify({"votes": vote_map, "voters": voters})


@app.route("/vote/result", methods=["GET"])
def vote_result():
    global vote_map, voters
    if not vote_map:
        return jsonify({"winner": None})
    winner = max(vote_map, key=vote_map.get)
    if vote_map[winner] == 0:
        return jsonify({"winner": None, "votes": vote_map})
    return jsonify({
        "winner": winner,
        "votes": vote_map,
        "voters": voters,
        "correct_voters": voters.get(winner, [])
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "collections": len(collections), "skins": len(all_skins)})


@app.route("/overwolf", methods=["POST"])
def overwolf_event():
    global state
    if state != "idle":
        return jsonify({"error": "quiz already running"}), 409
    data = request.get_json(force=True)
    event_type = data.get("event", "")
    if event_type == "kills" and data.get("count", 0) >= 3:
        return next_round()
    return jsonify({"ok": True, "ignored": True})


if __name__ == "__main__":
    load_data()
    print(f"Loaded {len(collections)} collections, {len(all_skins)} skins")
    app.run(host="0.0.0.0", port=8081, debug=False)
