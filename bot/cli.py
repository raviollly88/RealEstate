"""Консольная версия: python bot/cli.py Москва 90000000 80"""
import sys
from matcher import normalize_city, pick, format_matches


def main():
    if len(sys.argv) == 4:
        raw_city, b, a = sys.argv[1:]
    else:
        raw_city = input("Город (Сочи / Москва / Санкт-Петербург): ")
        b = input("Бюджет, ₽: ")
        a = input("Площадь, м²: ")
    city = normalize_city(raw_city)
    if not city:
        sys.exit("Город не найден. Доступно: Сочи, Москва, Санкт-Петербург")
    budget, area = float(b.replace(" ", "")), float(a.replace(",", "."))
    print(format_matches(pick(city, budget, area), city, budget, area))


if __name__ == "__main__":
    main()
