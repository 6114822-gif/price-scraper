import argparse
import csv
import re
import time

import requests
from bs4 import BeautifulSoup

# Сайт специально сделан для тренировки парсинга — можно скрейпить без ограничений
BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"

HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraper demo)"}

RATING_WORDS = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def fetch_page(page_number: int) -> str | None:
    url = BASE_URL.format(page_number)
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    books = []

    for card in soup.select("article.product_pod"):
        title = card.h3.a["title"]

        price_text = card.select_one(".price_color").text
        price = float(re.search(r"[\d.]+", price_text).group())

        availability = card.select_one(".availability").text.strip()

        rating_word = card.select_one("p.star-rating")["class"][1]
        rating = RATING_WORDS.get(rating_word, 0)

        books.append(
            {
                "title": title,
                "price_gbp": price,
                "availability": availability,
                "rating": rating,
            }
        )

    return books


def scrape(pages: int) -> list[dict]:
    all_books = []

    for page_number in range(1, pages + 1):
        html = fetch_page(page_number)
        if html is None:
            print(f"Страница {page_number} не найдена — останавливаюсь.")
            break

        books = parse_page(html)
        all_books.extend(books)
        print(f"Страница {page_number}: собрано {len(books)} книг")

        time.sleep(1)  # вежливая пауза, чтобы не перегружать сайт

    return all_books


def save_to_csv(books: list[dict], filename: str) -> None:
    if not books:
        print("Нечего сохранять — список пуст.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=books[0].keys())
        writer.writeheader()
        writer.writerows(books)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Собирает названия, цены и рейтинги книг с books.toscrape.com"
    )
    parser.add_argument(
        "--pages", type=int, default=5, help="сколько страниц каталога собрать (по умолчанию 5)"
    )
    parser.add_argument(
        "--output", default="books.csv", help="имя файла для сохранения (по умолчанию books.csv)"
    )
    args = parser.parse_args()

    books = scrape(args.pages)
    save_to_csv(books, args.output)

    print(f"\nГотово! Всего собрано {len(books)} книг. Сохранено в {args.output}")


if __name__ == "__main__":
    main()
