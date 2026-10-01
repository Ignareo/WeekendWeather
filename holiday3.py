# 国庆假期连续三天窗口分析（实时数据）
import csv, sys
from collections import defaultdict

# 与项目一致的雨况档位：取白天/夜间/降水中最严重者
def day_tier(day_text, night_text, precip):
    tier = 0
    for t in (day_text, night_text):
        if any(k in t for k in ("大雨", "暴雨")): tier = max(tier, 3)
        elif any(k in t for k in ("中雨", "雷阵雨", "中雪")): tier = max(tier, 2)
        elif any(k in t for k in ("小雨", "阵雨", "小雪")): tier = max(tier, 1)
    if precip >= 25: tier = max(tier, 3)
    elif precip >= 10: tier = max(tier, 2)
    elif precip >= 0.1: tier = max(tier, 1)
    return tier

TIER_ICON = ["☀️", "🌦", "🌧", "⛈"]
HOLIDAY = [f"2026-10-0{i}" for i in range(1, 8)]  # 10.1-10.7
N = int(sys.argv[2]) if len(sys.argv) > 2 else 3  # 连续 N 天

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
cities = defaultdict(dict)
for r in rows:
    d = r["日期"]
    if d in HOLIDAY:
        cities[r["城市"]][d] = {
            "tier": day_tier(r["白天天气"], r["夜间天气"], float(r["降水量(mm)"] or 0)),
            "precip": float(r["降水量(mm)"] or 0),
            "high": int(r["白天温度"]), "low": int(r["夜间温度"]),
            "day": r["白天天气"], "night": r["夜间天气"],
        }

results = []
for city, days in cities.items():
    if len(days) < len(HOLIDAY):  # 预报未覆盖整个假期（如假期中段打开）
        continue
    best = None
    for i in range(len(HOLIDAY) - N + 1):
        win = [days[d] for d in HOLIDAY[i:i + N]]
        key = (max(w["tier"] for w in win),              # 最差天雨况（行程下限）
               sum(w["precip"] for w in win),            # 总降水
               -sum(1 for w in win if w["tier"] == 0))   # 无雨天数多者优先
        if best is None or key < best[0]:
            best = (key, HOLIDAY[i], HOLIDAY[i + N - 1], win)
    key, d1, d2, win = best
    results.append({
        "city": city, "start": d1[5:], "end": d2[5:],
        "worst": TIER_ICON[key[0]], "precip": key[1],
        "icons": "".join(TIER_ICON[w["tier"]] for w in win),
        "highs": max(w["high"] for w in win), "lows": min(w["low"] for w in win),
        "detail": " ".join(f"{w['day']}/{w['night']}" for w in win),
    })

# 排序：最差天雨况 → 总降水 → 最高温低
results.sort(key=lambda r: (["☀️","🌦","🌧","⛈"].index(r["worst"]), r["precip"], r["highs"]))
print(f"{'城市':<6}{'最佳窗口':<12}{f'{N}天雨况':<10}{'综合':<5}{'总降水':<8}{'气温':<12}")
for r in results:
    print(f"{r['city']:<6}{r['start']}~{r['end']:<8}{r['icons']:<10}{r['worst']:<5}"
          f"{r['precip']:<6.1f}mm  {r['lows']}~{r['highs']}°C")
