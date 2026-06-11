#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import sys
from pathlib import Path
from collections import defaultdict

import pygame

ROOT = Path(__file__).resolve().parent
MAPPING_FILE = ROOT / "collection_mapping.json"
IMG_DIR = ROOT / "img"
SFX_DIR = ROOT / "sfx"

WIN_W, WIN_H = 1200, 700
BG_COLOR = (30, 30, 47)
GOLD = (255, 217, 102)
WHITE = (255, 255, 255)
GRAY = (100, 100, 120)
GREEN = (80, 200, 120)
RED = (220, 70, 70)
CARD_BG = (42, 42, 58)
CARD_BORDER = (80, 80, 110)
CARD_HOVER = (70, 70, 100)
IMG_SIZE = (220, 220)
ROUNDS = 10


def load_collections():
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    valid = []
    for col in data:
        sfx = Path(col["sfx"]) if col.get("sfx") else None
        if sfx and sfx.exists() and col.get("skins"):
            valid.append({
                "collection": col["collection"],
                "sfx": str(sfx),
                "skins": col["skins"],
            })
    return valid


def build_questions(collections):
    all_skins = []
    for col in collections:
        for skin in col["skins"]:
            img = Path(skin["image"])
            if img.exists():
                all_skins.append({
                    "collection": col["collection"],
                    "weapon": skin["weapon"],
                    "image": str(img),
                    "sfx": col["sfx"],
                })
    if not all_skins:
        return []

    by_weapon = defaultdict(list)
    for s in all_skins:
        by_weapon[s["weapon"]].append(s)

    questions = []
    for col in collections:
        col_skins = [s for s in all_skins if s["collection"] == col["collection"]]
        if not col_skins:
            continue
        correct = random.choice(col_skins)
        weapon = correct["weapon"]
        candidates = [s for s in by_weapon[weapon] if s["collection"] != col["collection"]]
        if len(candidates) < 3:
            candidates += [s for s in all_skins if s["collection"] != col["collection"]]
        if len(candidates) < 3:
            continue
        distractors = random.sample(candidates, 3)
        options = distractors + [correct]
        random.shuffle(options)
        questions.append({
            "collection": col["collection"],
            "weapon": weapon,
            "sfx": col["sfx"],
            "correct": correct,
            "options": options,
        })
    return questions


def draw_text(surface, text, font, color, x, y, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(x, y) if center else (x, y))
    surface.blit(rendered, rect)


def play_sound(path):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()


def run_quiz():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Valorant Skin Quiz")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("Arial", 36, bold=True)
    font_med = pygame.font.SysFont("Arial", 24)
    font_sm = pygame.font.SysFont("Arial", 18)

    collections = load_collections()
    if not collections:
        print("Нет подходящих коллекций.")
        pygame.quit()
        return

    questions = build_questions(collections)
    if not questions:
        print("Не удалось сгенерировать вопросы.")
        pygame.quit()
        return

    random.shuffle(questions)
    selected = questions[:min(ROUNDS, len(questions))]
    score = 0
    state = "playing"
    feedback_correct = False
    q_idx = 0
    current_q = selected[q_idx]
    hovered = -1
    selected_opt = -1
    sound_played = False

    skin_cache = {}

    def load_skin_image(path):
        if path in skin_cache:
            return skin_cache[path]
        try:
            img = pygame.image.load(path).convert_alpha()
            w, h = img.get_size()
            max_w, max_h = 210, 210
            scale = min(max_w / w, max_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = pygame.transform.smoothscale(img, (new_w, new_h))
            skin_cache[path] = img
            return img
        except Exception:
            surf = pygame.Surface(IMG_SIZE)
            surf.fill(GRAY)
            skin_cache[path] = surf
            return surf

    def start_question(idx):
        nonlocal current_q, hovered, selected_opt, sound_played
        current_q = selected[idx]
        hovered = -1
        selected_opt = -1
        sound_played = False

    def restart_quiz():
        nonlocal questions, selected, score, state, q_idx, feedback_correct
        nonlocal hovered, selected_opt, sound_played
        pygame.mixer.music.stop()
        questions = build_questions(collections)
        if not questions:
            return
        random.shuffle(questions)
        selected = questions[:min(ROUNDS, len(questions))]
        score = 0
        state = "playing"
        feedback_correct = False
        q_idx = 0
        start_question(0)

    restart_quiz()

    running = True
    while running:
        clock.tick(60)
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "feedback":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    restart_quiz()
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    q_idx += 1
                    if q_idx >= len(selected):
                        state = "result"
                    else:
                        start_question(q_idx)
                        state = "playing"
                continue

            if state == "result":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    restart_quiz()
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    running = False
                continue

            if state == "playing":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    restart_quiz()
                    continue

                if not sound_played:
                    play_sound(current_q["sfx"])
                    sound_played = True

                if event.type == pygame.MOUSEMOTION:
                    hovered = -1
                    for i in range(4):
                        bx = 120 + i * 260
                        by = 300
                        card_rect = pygame.Rect(bx, by, 240, 340)
                        if card_rect.collidepoint(mouse):
                            hovered = i

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i in range(4):
                        bx = 120 + i * 260
                        by = 300
                        card_rect = pygame.Rect(bx, by, 240, 340)
                        if card_rect.collidepoint(mouse):
                            selected_opt = i
                            chosen = current_q["options"][i]
                            feedback_correct = chosen["collection"] == current_q["collection"]
                            if feedback_correct:
                                score += 1
                            pygame.mixer.music.stop()
                            state = "feedback"
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        selected_opt = 0
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        selected_opt = 1
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        selected_opt = 2
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        selected_opt = 3
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        selected_opt = 0
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        selected_opt = 1
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        selected_opt = 2
                    elif event.key in (pygame.K_f, pygame.K_UP):
                        selected_opt = 3
                    else:
                        continue

                    chosen = current_q["options"][selected_opt]
                    feedback_correct = chosen["collection"] == current_q["collection"]
                    if feedback_correct:
                        score += 1
                    pygame.mixer.music.stop()
                    state = "feedback"

        screen.fill(BG_COLOR)

        if state == "playing":
            draw_text(screen, f"Раунд {q_idx + 1}/{len(selected)}", font_med, GRAY, WIN_W // 2, 30, center=True)
            draw_text(screen, f"Оружие: {current_q['weapon']}", font_big, GOLD, WIN_W // 2, 80, center=True)
            draw_text(screen, "Какой скин соответствует звуку?", font_med, WHITE, WIN_W // 2, 140, center=True)
            draw_text(screen, "Нажми 1-4 или A/S/D/F", font_sm, GRAY, WIN_W // 2, 180, center=True)
            draw_text(screen, "R — начать заново", font_sm, GRAY, WIN_W // 2, 210, center=True)

            for i, opt in enumerate(current_q["options"]):
                bx = 120 + i * 260
                by = 300
                card_rect = pygame.Rect(bx, by, 240, 340)

                border_color = CARD_HOVER if i == hovered else CARD_BORDER

                pygame.draw.rect(screen, CARD_BG, card_rect, border_radius=12)
                pygame.draw.rect(screen, border_color, card_rect, 3, border_radius=12)

                img = load_skin_image(opt["image"])
                img_rect = img.get_rect(center=(bx + 120, by + 110))
                screen.blit(img, img_rect)

                num_rect = pygame.Rect(bx + 90, by + 280, 60, 40)
                pygame.draw.rect(screen, border_color, num_rect, border_radius=8)
                draw_text(screen, str(i + 1), font_med, WHITE, bx + 120, by + 300, center=True)
                draw_text(screen, opt["collection"], font_sm, GOLD, bx + 120, by + 240, center=True)

            draw_text(screen, f"Счёт: {score}", font_med, GREEN, 80, 660)

        elif state == "feedback":
            draw_text(screen, f"Раунд {q_idx + 1}/{len(selected)}", font_med, GRAY, WIN_W // 2, 30, center=True)
            draw_text(screen, f"Оружие: {current_q['weapon']}", font_big, GOLD, WIN_W // 2, 80, center=True)

            if feedback_correct:
                draw_text(screen, "Правильно!", font_big, GREEN, WIN_W // 2, 150, center=True)
            else:
                chosen = current_q["options"][selected_opt]
                draw_text(screen, f"Неверно! Правильно: {current_q['collection']}", font_big, RED, WIN_W // 2, 150, center=True)

            for i, opt in enumerate(current_q["options"]):
                bx = 120 + i * 260
                by = 280
                card_rect = pygame.Rect(bx, by, 240, 340)

                if i == selected_opt:
                    border_color = GREEN if feedback_correct else RED
                elif opt["collection"] == current_q["collection"]:
                    border_color = GREEN
                else:
                    border_color = CARD_BORDER

                pygame.draw.rect(screen, CARD_BG, card_rect, border_radius=12)
                pygame.draw.rect(screen, border_color, card_rect, 3, border_radius=12)

                img = load_skin_image(opt["image"])
                img_rect = img.get_rect(center=(bx + 120, by + 110))
                screen.blit(img, img_rect)

                draw_text(screen, str(i + 1), font_med, WHITE, bx + 120, by + 300, center=True)
                draw_text(screen, opt["collection"], font_sm, GOLD, bx + 120, by + 240, center=True)

            draw_text(screen, "Нажми любую клавишу или кликни", font_sm, GRAY, WIN_W // 2, 660, center=True)
            draw_text(screen, f"Счёт: {score}", font_med, GREEN, 80, 660)

        elif state == "result":
            draw_text(screen, "Викторина окончена!", font_big, GOLD, WIN_W // 2, 200, center=True)
            draw_text(screen, f"Счёт: {score} из {len(selected)}", font_big, WHITE, WIN_W // 2, 280, center=True)
            pct = score / len(selected) * 100 if selected else 0
            if pct == 100:
                msg = "Идеально! Ты эксперт по скинам."
            elif pct >= 50:
                msg = "Хороший результат, но есть куда расти."
            else:
                msg = "В следующий раз повезёт больше!"
            draw_text(screen, msg, font_med, GREEN if pct >= 50 else RED, WIN_W // 2, 360, center=True)
            draw_text(screen, "Нажми любую клавишу или кликни для выхода", font_sm, GRAY, WIN_W // 2, 640, center=True)
            draw_text(screen, "R — начать заново", font_sm, GRAY, WIN_W // 2, 680, center=True)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run_quiz()
