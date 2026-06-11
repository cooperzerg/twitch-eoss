import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent

IMG_DIR = ROOT / "img"
SFX_DIR = ROOT / "sfx"

# ===== Сбор данных =====
print("🔍 Анализируем папки...")

# --- 1. Обрабатываем звуки (sfx) ---
sfx_files = list(SFX_DIR.glob("*.mp3"))
sfx_map = {}  # коллекция -> путь к звуку
for sfx_path in sfx_files:
    stem = sfx_path.stem  # имя без расширения, например "Aemondir"
    sfx_map[stem] = sfx_path

print(f"📢 Найдено звуков: {len(sfx_map)}")

# --- 2. Обрабатываем изображения скинов (img) ---
img_files = list(IMG_DIR.glob("*.webp"))
# Дополнительно поддержим .png, если есть
img_files += list(IMG_DIR.glob("*.png"))

collection_weapons = defaultdict(list)  # коллекция -> список оружий
weapon_count = defaultdict(int)         # оружие -> количество (сколько разных коллекций)

for img_path in img_files:
    name = img_path.stem  # "Aemondir_Sheriff"
    # Разделяем по первому подчёркиванию
    if "_" in name:
        collection, weapon = name.split("_", 1)
    else:
        # если нет подчёркивания – пропускаем
        continue
    collection_weapons[collection].append(weapon)
    weapon_count[weapon] += 1

print(f"🖼️ Найдено изображений: {len(img_files)}")
print(f"🎨 Уникальных коллекций (по изображениям): {len(collection_weapons)}")

# ===== Статистика по оружию =====
print("\n📊 Статистика по оружию (сколько разных коллекций имеют это оружие):")
for weapon, cnt in sorted(weapon_count.items(), key=lambda x: -x[1]):
    print(f"   {weapon}: {cnt}")

# ===== Формируем JSON =====
result = []
all_collections = set(sfx_map.keys()) | set(collection_weapons.keys())

for collection in sorted(all_collections):
    entry = {
        "collection": collection,
        "sfx": str(sfx_map.get(collection)) if collection in sfx_map else None,
        "skins": []
    }
    for weapon in collection_weapons.get(collection, []):
        entry["skins"].append({
            "weapon": weapon,
            "image": str(IMG_DIR / f"{collection}_{weapon}.webp")
        })
    result.append(entry)

# Сохраняем JSON
output_path = ROOT / "collection_mapping.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n✅ JSON сохранён: {output_path}")

# ===== Дополнительная сводка =====
collections_with_both = set(sfx_map.keys()) & set(collection_weapons.keys())
collections_missing_sfx = set(collection_weapons.keys()) - set(sfx_map.keys())
collections_missing_img = set(sfx_map.keys()) - set(collection_weapons.keys())

print("\n📌 Сводка:")
print(f"   Коллекций, у которых есть и звук, и хотя бы один скин: {len(collections_with_both)}")
print(f"   Коллекций, у которых есть скины, но нет звука: {len(collections_missing_sfx)}")
if collections_missing_sfx:
    print(f"     Примеры: {', '.join(list(collections_missing_sfx)[:5])}")
print(f"   Коллекций, у которых есть звук, но нет ни одного скина: {len(collections_missing_img)}")
if collections_missing_img:
    print(f"     Примеры: {', '.join(list(collections_missing_img)[:5])}")
