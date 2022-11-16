import sys
from time import sleep

import requests
from bs4 import BeautifulSoup
import re


class Book:
    def __init__(self, title: str, author: str, read: str, asin: str, book_format: str, comment: list):
        self.title = title
        self.author = author
        self.read = read
        self.asin = asin
        self.book_format = book_format
        self.comment = comment

    def __str__(self):
        s = '''## {title}
読了日:{read} 著者:{author}

[asin:{asin}:detail]

{comment}
'''.format(
            title=self.title,
            read=self.read,
            author=self.author,
            asin=self.asin,
            comment="\n".join(self.comment),
        )

        return s


class BookmeterSummary:
    def __init__(self, date: str, count: int, pages: int, link: str):
        self.date = date
        self.count = count
        self.pages = pages
        self.link = link
        self.books = []

    def add_book(self, book):
        self.books.append(book)

    def filter(self, book_format):
        return [book for book in self.books if book.book_format == book_format]

    def __str__(self):
        s = f'''<!-- more -->

- {self.date}の読書メーター
- 読んだ本の数：{self.count}冊
- 読んだページ数：{self.pages}ページ

[{self.link}:embed:cite]

# Kindle
{''.join([str(book) for book in self.filter('Kindle')])}
# Kindle Unlimited

# Audible
{''.join([str(book) for book in self.filter('Audible')])}

# 大学図書館

----

- 今月の最も良かった本は、「###」
- [memo]'''

        return s


def main():
    summary = parse_bookmeter_summary(sys.stdin.readlines())

    print(summary)


def parse_bookmeter_summary(lines) -> BookmeterSummary:
    summary = BookmeterSummary('', 0, 0, '')
    lines = [line for line in [line.strip() for line in lines] if line != '']
    for line in lines:
        if line.startswith('https://bookmeter.com/users/'):
            summary.link = line
        elif line.endswith('の読書メーター'):
            summary.date = re.match(r'(\d+年\d+月)の読書メーター', line).group(1)
        elif line.startswith('読んだ本'):
            summary.count = int(re.match(r'読んだ本の数：(\d+)冊', line).group(1))
        elif line.startswith('読んだページ'):
            summary.pages = int(re.match(r'読んだページ数：(\d+)ページ', line).group(1))

    for i in range(len(lines)):
        if lines[i].startswith('■'):
            title_index = i
            title = lines[title_index].replace('■', '').strip()

            tmp_i = title_index + 1
            while not lines[tmp_i].startswith('https://bookmeter.com/books/'):
                tmp_i += 1
            bookmeter_url = lines[tmp_i]
            asin = bookmeter_url_to_asin(bookmeter_url)
            book_format = get_book_format_by_asin(asin)
            read, author = re.match(r'読了日:(.*) 著者:(.*)', lines[tmp_i - 1]).groups()

            if title_index != i - 2:
                comment = lines[title_index + 1:tmp_i - 1]
            else:
                comment = []

            book = Book(title, author, read, asin, book_format, comment)
            summary.add_book(book)

    return summary


def bookmeter_url_to_asin(bookmeter_url):
    response = requests.get(bookmeter_url)
    sleep(1)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        amazon_link = soup.find('a', class_='image__cover')['href'].split('?')[0]
        amazon_link = re.sub(r'/ref=.*', '', amazon_link)

        asin = amazon_link.split('/')[-1]
        return asin

    return ''


def get_book_format_by_asin(asin):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36', }
    response = requests.get('https://www.amazon.co.jp/dp/' + asin, headers=headers)
    sleep(1)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        product_subtitle = soup.find('span', id='productSubtitle')
        if product_subtitle is not None:
            return product_subtitle.text.strip()[0:-1]

        product_binding = soup.find('span', id='productBinding')
        if product_binding is not None:
            return product_binding.text.strip()[0:-1]

    return ''


if __name__ == '__main__':
    main()
