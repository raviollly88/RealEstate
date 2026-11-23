"""График: цена «от» за м² по 15 ЖК и 3 городам. Запуск: python analysis/chart.py"""
import csv
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent.parent
with open(root / "data" / "complexes.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["p"] = float(r["price_per_m2_from"])

colors = {"Сочи": "#2563eb", "Москва": "#dc2626", "Санкт-Петербург": "#059669"}
rows.sort(key=lambda r: (list(colors).index(r["city"]), r["p"]))

plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(12, 7.2), facecolor="#ffffff")
ax.set_facecolor("#f8fafc")

labels = [f'{r["name"]} ({r["class"]})' for r in rows]
bars = ax.barh(labels, [r["p"] / 1000 for r in rows], color=[colors[r["city"]] for r in rows], height=0.66, edgecolor="none")

for b, r in zip(bars, rows):
    val = f'{r["p"]/1000:,.0f} тыс.'.replace(",", " ")
    ax.text(b.get_width() + 35, b.get_y() + b.get_height() / 2, val, va="center", fontsize=8.5, color="#1e293b", fontweight="bold")

ax.set_xlim(0, max(r["p"] / 1000 for r in rows) * 1.16)
ax.grid(axis="x", linestyle="--", alpha=0.45, color="#94a3b8")
ax.set_axisbelow(True)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color("#cbd5e1")
ax.spines["bottom"].set_color("#cbd5e1")

ax.set_xlabel("Цена «от», тыс. ₽ за м²", fontsize=10, fontweight="bold", color="#0f172a", labelpad=8)
ax.set_title("Рынок новостроек: цена «от» за м² (бизнес и премиум)", fontsize=13, fontweight="bold", color="#0f172a", loc="left", pad=22)
fig.text(0.125, 0.915, "15 ЖК в Сочи, Москве и Санкт-Петербурге · источники: ЦИАН, сайты застройщиков · 23.11.2026", fontsize=9, color="#475569")

handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
ax.legend(handles, list(colors.keys()), frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", loc="lower right", fontsize=9.5)
ax.invert_yaxis()
plt.tight_layout(rect=[0, 0, 1, 0.91])
plt.savefig(root / "analysis" / "price_chart.png", dpi=160)

print("city, median, min, max (₽/м²)")
for c in colors:
    v = [r["p"] for r in rows if r["city"] == c]
    print(c, int(st.median(v)), int(min(v)), int(max(v)))
