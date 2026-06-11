# !quiz{n} Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `!quiz{n}` command to Streamer.bot that triggers a Valorant skin sound quiz with n questions, real-time chat voting, and result display.

**Architecture:** Streamer.bot command calls Flask server API, server manages quiz state, overlay displays questions/votes/results, chat votes A/B/C/D in real-time.

**Tech Stack:** Python (Flask), C# (Streamer.bot actions), HTML/CSS/JS (OBS overlay)

---

### Task 1: Add Overwolf Endpoint to Server

**Covers:** [S1]

**Files:**
- Modify: `sound-skins-quiz/server.py`

- [ ] **Step 1: Add /overwolf endpoint**

Add after the `/health` endpoint:

```python
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
```

- [ ] **Step 2: Test server starts**

Run: `cd sound-skins-quiz && python server.py`
Expected: "Loaded 61 collections, 140 skins"

- [ ] **Step 3: Test /overwolf endpoint**

Run: `curl -X POST http://localhost:8080/overwolf -H "Content-Type: application/json" -d '{"event":"kills","count":3}'`
Expected: JSON response with weapon, sfx_url, options

- [ ] **Step 4: Commit**

```bash
git add sound-skins-quiz/server.py
git commit -m "feat: add /overwolf endpoint for Overwolf integration"
```

---

### Task 2: Create Streamer.bot Quiz Action

**Covers:** [S2]

**Files:**
- Modify: `streamerbot/data/actions.json`

- [ ] **Step 1: Create quiz_trigger action**

Add to actions.json in the "actions" array:

```json
{
  "id": "quiz-trigger-001",
  "queue": "00000000-0000-0000-0000-000000000000",
  "enabled": true,
  "excludeFromHistory": false,
  "excludeFromPending": false,
  "name": "quiz_trigger",
  "group": "Quiz",
  "alwaysRun": false,
  "randomAction": false,
  "concurrent": false,
  "triggers": [],
  "subActions": [
    {
      "name": "HTTP Request",
      "description": "Call quiz server",
      "actionType": "Core",
      "actionId": "HTTP Request"
    }
  ]
}
```

- [ ] **Step 2: Create quiz_vote action**

Add to actions.json:

```json
{
  "id": "quiz-vote-001",
  "queue": "00000000-0000-0000-0000-000000000000",
  "enabled": true,
  "excludeFromHistory": false,
  "excludeFromPending": false,
  "name": "quiz_vote",
  "group": "Quiz",
  "alwaysRun": false,
  "randomAction": false,
  "concurrent": false,
  "triggers": [],
  "subActions": []
}
```

- [ ] **Step 3: Verify JSON is valid**

Run: `python -c "import json; json.load(open('streamerbot/data/actions.json','r',encoding='utf-8-sig')); print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add streamerbot/data/actions.json
git commit -m "feat: add quiz_trigger and quiz_vote actions"
```

---

### Task 3: Create Streamer.bot Quiz Command

**Covers:** [S2]

**Files:**
- Modify: `streamerbot/data/commands.json`

- [ ] **Step 1: Add !quiz command**

Add to commands.json in the "commands" array:

```json
{
  "id": "quiz-cmd-001",
  "name": "Quiz",
  "enabled": true,
  "include": true,
  "mode": 2,
  "command": "!quiz",
  "regexExplicitCapture": false,
  "location": 0,
  "ignoreBotAccount": true,
  "ignoreInternal": true,
  "sources": 1,
  "persistCounter": false,
  "persistUserCounter": false,
  "caseSensitive": false,
  "globalCooldown": 0,
  "userCooldown": 0,
  "group": "Quiz",
  "grantType": 0
}
```

- [ ] **Step 2: Verify JSON is valid**

Run: `python -c "import json; json.load(open('streamerbot/data/commands.json','r',encoding='utf-8-sig')); print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add streamerbot/data/commands.json
git commit -m "feat: add !quiz command"
```

---

### Task 4: Add Vote Tracking to Server

**Covers:** [S3]

**Files:**
- Modify: `sound-skins-quiz/server.py`

- [ ] **Step 1: Add voters tracking**

Add after `vote_map` initialization:

```python
voters = {"A": [], "B": [], "C": [], "D": []}
```

- [ ] **Step 2: Update /vote/chat to track voters**

Replace the `/vote/chat` endpoint:

```python
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
```

- [ ] **Step 3: Update /vote/result to include voters**

Replace the `/vote/result` endpoint:

```python
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
```

- [ ] **Step 4: Reset voters on new round**

Update the `/next_round` endpoint to reset voters:

```python
@app.route("/next_round", methods=["POST"])
def next_round():
    global current_question, current_options, state, vote_map, voters
    q = generate_question()
    if not q:
        return jsonify({"error": "no questions available"}), 500

    current_question = q
    current_options = q["options"]
    state = "playing"
    vote_map = {"A": 0, "B": 0, "C": 0, "D": 0}
    voters = {"A": [], "B": [], "C": [], "D": []}

    return jsonify({
        "weapon": q["weapon"],
        "sfx_url": q["sfx_url"],
        "options": [{"label": o["label"], "collection": o["collection"], "image_url": o["image_url"]} for o in q["options"]],
    })
```

- [ ] **Step 5: Test vote tracking**

Run: `curl -X POST http://localhost:8080/vote/chat -H "Content-Type: application/json" -d '{"char":"a","username":"test_user"}'`
Expected: `{"votes": {"A": 1, "B": 0, "C": 0, "D": 0}, "voters": {"A": ["test_user"], "B": [], "C": [], "D": []}}`

- [ ] **Step 6: Commit**

```bash
git add sound-skins-quiz/server.py
git commit -m "feat: add voter tracking to quiz server"
```

---

### Task 5: Update Overlay for Results

**Covers:** [S4]

**Files:**
- Modify: `sound-skins-quiz/static/index.html`

- [ ] **Step 1: Update renderFeedback function**

Replace the `renderFeedback` function:

```javascript
function renderFeedback(data) {
  let html = `<div class="weapon-label">${data.weapon}</div>`;
  html += `<div class="result-text">Правильный ответ: ${data.correct_collection}</div>`;
  html += `<div class="cards">`;
  for (const opt of data.options) {
    let cls = '';
    if (opt.label === data.correct_label) cls = 'correct';
    html += `
      <div class="card ${cls}">
        <div class="label">${opt.label}</div>
        <img src="${opt.image_url}" alt="${opt.collection}">
        <div class="name">${opt.collection}</div>
      </div>`;
  }
  html += `</div>`;
  
  if (data.correct_voters && data.correct_voters.length > 0) {
    html += `<div class="voters">Угадали: ${data.correct_vouters.join(', ')}</div>`;
  } else {
    html += `<div class="voters">Никто не угадал</div>`;
  }
  
  html += `<div class="score">${data.score || 0} / ${data.total || 0}</div>`;
  app.innerHTML = html;
}
```

- [ ] **Step 2: Add voters CSS**

Add to the `<style>` section:

```css
.voters {
  color: rgba(255,255,255,0.7);
  font-size: 18px;
  margin-top: 10px;
  text-align: center;
}
```

- [ ] **Step 3: Test overlay**

Open `http://localhost:8080` in browser
Expected: Overlay shows "Ожидание..."

- [ ] **Step 4: Commit**

```bash
git add sound-skins-quiz/static/index.html
git commit -m "feat: update overlay to show correct voters"
```

---

### Task 6: Add Quiz State Management

**Covers:** [S5]

**Files:**
- Modify: `sound-skins-quiz/server.py`

- [ ] **Step 1: Add quiz state variables**

Add after `voters` initialization:

```python
quiz_round = 0
quiz_total = 0
```

- [ ] **Step 2: Update /next_round to track rounds**

Replace the `/next_round` endpoint:

```python
@app.route("/next_round", methods=["POST"])
def next_round():
    global current_question, current_options, state, vote_map, voters, quiz_round, quiz_total
    data = request.get_json(force=True) if request.is_json else {}
    
    if state == "idle":
        quiz_total = data.get("questions", 1)
        quiz_round = 0
    
    if quiz_round >= quiz_total:
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
```

- [ ] **Step 3: Update /state to include round info**

Update the `/state` endpoint:

```python
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
```

- [ ] **Step 4: Update /reset to reset quiz state**

Update the `/reset` endpoint:

```python
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
```

- [ ] **Step 5: Test multi-round quiz**

Run: `curl -X POST http://localhost:8080/next_round -H "Content-Type: application/json" -d '{"questions":3}'`
Expected: `{"round": 1, "total": 3, "weapon": "...", ...}`

- [ ] **Step 6: Commit**

```bash
git add sound-skins-quiz/server.py
git commit -m "feat: add multi-round quiz state management"
```

---

### Task 7: Update Overlay for Round Info

**Covers:** [S5]

**Files:**
- Modify: `sound-skins-quiz/static/index.html`

- [ ] **Step 1: Update renderPlaying function**

Replace the `renderPlaying` function:

```javascript
function renderPlaying(data) {
  let html = `<div class="weapon-label">${data.weapon}</div>`;
  html += `<div class="round-info">Раунд ${data.round || 1} из ${data.total_rounds || 1}</div>`;
  html += `<div class="timer-bar"><div class="timer-fill" id="timer"></div></div>`;
  html += `<div class="cards">`;
  for (const opt of data.options) {
    html += `
      <div class="card">
        <div class="label">${opt.label}</div>
        <img src="${opt.image_url}" alt="${opt.collection}">
        <div class="name">${opt.collection}</div>
      </div>`;
  }
  html += `</div>`;
  html += `<div class="score">${data.score || 0} / ${data.total || 0}</div>`;
  app.innerHTML = html;
}
```

- [ ] **Step 2: Add round-info CSS**

Add to the `<style>` section:

```css
.round-info {
  color: rgba(255,255,255,0.5);
  font-size: 16px;
  margin-bottom: 8px;
}
```

- [ ] **Step 3: Commit**

```bash
git add sound-skins-quiz/static/index.html
git commit -m "feat: update overlay to show round info"
```

---

### Task 8: Test Full Integration

**Covers:** [S1, S2, S3, S4, S5]

**Files:**
- None (testing only)

- [ ] **Step 1: Start server**

Run: `cd sound-skins-quiz && python server.py`
Expected: Server running on http://localhost:8080

- [ ] **Step 2: Test quiz flow**

Run: `curl -X POST http://localhost:8080/next_round -H "Content-Type: application/json" -d '{"questions":2}'`
Expected: Round 1 question

- [ ] **Step 3: Test vote**

Run: `curl -X POST http://localhost:8080/vote/chat -H "Content-Type: application/json" -d '{"char":"a","username":"test_user"}'`
Expected: Vote recorded

- [ ] **Step 4: Test result**

Run: `curl http://localhost:8080/vote/result`
Expected: Winner and voters

- [ ] **Step 5: Test next round**

Run: `curl -X POST http://localhost:8080/next_round`
Expected: Round 2 question

- [ ] **Step 6: Test quiz finish**

Run: `curl -X POST http://localhost:8080/next_round`
Expected: Quiz finished message

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "test: verify full quiz integration"
```
