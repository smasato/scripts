import sys
import requests
from bs4 import BeautifulSoup
import re


def main(argv):
    lines = sys.stdin.readlines()

    lines = [replace_bookmeter_url(line) for line in lines]
    lines = [line.replace('■', '## ') if line.startswith('■') else line for line in lines]
    lines = [line for line in lines if not line.startswith('ナイス数')]
    lines = ['- ' + line if line.startswith('読んだ') else line for line in lines]
    lines = ['- ' + line if line.endswith('の読書メーター\n') else line for line in lines]
    lines = ["[{}:embed:cite]\n".format(line.strip()) if 'summary' in line else line for line in lines]

    print("".join(lines))


def replace_bookmeter_url(line):
    if line.startswith('https://bookmeter.com/books/'):
        response = requests.get(line)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            amazon_link = soup.find('a', class_='image__cover')['href'].split('?')[0]
            amazon_link = re.sub(r'/ref=.*', '', amazon_link)

            asin = amazon_link.split('/')[-1]
            line = "[asin:{}:detail]\n".format(asin)
    return line


if __name__ == '__main__':
    main(sys.argv)
