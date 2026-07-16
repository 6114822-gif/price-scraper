import argparse
import csv
import re

import requests
from bs4 import BeautifulSoup

# Livelib.ru — русскоязычный сайт отзывов и рейтингов книг (не магазин).
# robots.txt сайта разрешает парсинг страниц жанров и книг (проверено 16.07.2026):
# запрещены только служебные подстраницы (/editions/, /tags/, /search и т.п.),
# сама страница жанра и карточки книг — разрешены.
GENRE_URL = "https://www.livelib.ru/genre/%D0%94%D0%B5%D1%82%D0%B5%D0%BA%D1%82%D0%B8%D0%B2%D1%8B/top"

HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraper demo)"}


def fetch_page() -> str:
    response = requests.get(GENRE_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_books(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    books = []

    for item in soup.select(".book-item__item")[:limit]:
        title_tag = item.select_one(".book-item__title")
        if not title_tag:
            continue

        author_tag = item.select_one(".book-item__author")
        rating_tag = item.select_one(".book-item__rating")
        readers_tag = item.select_one(".icon-added-grey")

        title = title_tag.get_text(strip=True)
        author = author_tag.get_text(strip=True) if author_tag else "не указан"

        rating_text = rating_tag.get_text(strip=True) if rating_tag else None
        rating = rating_text.replace(",", ".") if rating_text else "нет данных"

        # На карточке число округлено ("12K"), точное значение лежит в title
        # атрибуте ссылки (например: "11950 прочитали") — берём именно его.
        readers = "нет данных"
        if readers_tag and readers_tag.get("title"):
            match = re.search(r"[\d\s]+", readers_tag["title"])
            if match:
                readers = match.group().replace(" ", "").strip()

        books.append(
            {
                "название": title,
                "автор": author,
                "рейтинг": rating,
                "читателей": readers,
                "источник": "livelib.ru",
            }
        )

    return books


def save_to_csv(books: list[dict], filename: str) -> None:
    if not books:
        print("Нечего сохранять — список пуст.")
        return

    # utf-8-sig — чтобы кириллица корректно открывалась в Excel на Windows
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=books[0].keys())
        writer.writeheader()
        writer.writerows(books)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Собирает названия, авторов и рейтинги детективов с livelib.ru"
    )
    parser.add_argument(
        "--count", type=int, default=20, help="сколько книг собрать (по умолчанию 20)"
    )
    parser.add_argument(
        "--output", default="detectives.csv", help="имя файла для сохранения (по умолчанию detectives.csv)"
    )
    args = parser.parse_args()

    html = fetch_page()
    books = parse_books(html, args.count)
    save_to_csv(books, args.output)

    print(f"Готово! Собрано {len(books)} детективов. Сохранено в {args.output}")


if __name__ == "__main__":
    main()
