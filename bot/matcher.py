"""Логика подборщика ЖК: город + бюджет + площадь -> 3 ЖК из data/complexes.csv.

Только стандартная библиотека. Используется и в CLI (cli.py), и в Telegram-боте (bot.py).
"""
import csv
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "complexes.csv"

CITY_ALIASES = {
    "сочи": "Сочи",
    "москва": "Москва",
    "мск": "Москва",
    "санкт-петербург": "Санкт-Петербург",
    "спб": "Санкт-Петербург",
    "питер": "Санкт-Петербург",
    "петербург": "Санкт-Петербург",
}


@dataclass
class Complex:
    city: str
    name: str
    developer: str
    district: str
    cls: str
    price_m2: float
    delivery: str
    url: str
    min_area: float | None
    max_area: float | None
    area_est: bool = False


@dataclass
class Match:
    cx: Complex
    cost: float          # примерная стоимость квартиры = цена за м² от × площадь
    in_budget: bool
    area_ok: bool | None  # None — диапазон площадей на странице не указан


def normalize_city(text: str) -> str | None:
    return CITY_ALIASES.get(text.strip().lower())


def _f(v: str) -> float | None:
    v = v.strip().replace(",", ".")
    return float(v) if v else None


def load(path: Path = DATA) -> list[Complex]:
    with open(path, encoding="utf-8", newline="") as f:
        return [
            Complex(r["city"], r["name"], r["developer"], r["district"], r["class"],
                    float(r["price_per_m2_from"]), r["delivery"], r["source_url"],
                    _f(r["min_area_m2"]), _f(r["max_area_m2"]), r.get("area_estimated") == "1")
            for r in csv.DictReader(f)
        ]


MAX_OVER_BUDGET = 2_000_000


def pick(city: str, budget: float, area: float, k: int = 3,
         data: list[Complex] | None = None,
         max_over_budget: float = MAX_OVER_BUDGET) -> list[Match]:
    """Выбирает до k ЖК.

    1. В городе оставляем ЖК, где указанная площадь входит в диапазон (или диапазон неизвестен).
    2. Исключаем ЖК, где стоимость превышает бюджет более чем на max_over_budget (2 000 000 ₽).
    3. Сначала идут ЖК, где стоимость <= бюджета; среди них — ближайшие к бюджету.
    4. Если таких меньше k — добиваем ближайшими сверху (в пределах +2 млн ₽) и помечаем in_budget=False.
    """
    data = data if data is not None else load()
    res = []
    for c in data:
        if c.city != city:
            continue
        if c.min_area is not None and area < c.min_area:
            continue
        if c.max_area is not None and area > c.max_area:
            continue
        cost = c.price_m2 * area
        if cost > budget + max_over_budget:
            continue
        ok = not c.area_est and c.min_area is not None
        res.append(Match(c, cost, cost <= budget, ok))
    inside = sorted((m for m in res if m.in_budget), key=lambda m: budget - m.cost)
    above = sorted((m for m in res if not m.in_budget), key=lambda m: m.cost)
    return (inside + above)[:k]


def fmt_rub(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ") + " ₽"


def format_matches(matches: list[Match], city: str, budget: float, area: float) -> str:
    if not matches:
        return (f"В городе {city} нет подходящих ЖК для площади {area:g} м² "
                f"в пределах бюджета {fmt_rub(budget)} (+2 000 000 ₽ допустимого превышения). "
                "Увеличьте бюджет или уменьшите площадь.")
    lines = [f"Подбор: {city}, бюджет {fmt_rub(budget)}, площадь {area:g} м²\n"]
    for i, m in enumerate(matches, 1):
        c = m.cx
        flag = "✅ в бюджете" if m.in_budget else f"⚠️ дороже бюджета на {fmt_rub(m.cost - budget)}"
        note = "" if m.area_ok else "\n   ℹ️ диапазон площадей ориентировочный (в источнике не указан)"
        lines.append(
            f"{i}. {c.name} ({c.cls}), {c.district}\n"
            f"   ~{fmt_rub(m.cost)} · от {fmt_rub(c.price_m2)}/м² · сдача: {c.delivery}\n"
            f"   {flag}{note}\n   {c.url}"
        )
    lines.append("\nСтоимость примерная: цена «от» × площадь. Реальная цена зависит от этажа, вида и отделки.")
    return "\n".join(lines)
