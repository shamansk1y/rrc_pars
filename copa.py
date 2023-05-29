# -*- coding: utf-8 -*-

import bs4
import logging
import csv
import requests
from fake_useragent import UserAgent
import collections
import time

MANUFACTURER = 'joma'

logger = logging.getLogger('copa')
logging.basicConfig(level=logging.INFO)

ua = UserAgent()
headers = {'User-Agent': ua.random}
ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'model',
        'price_old',
        'price_new',
    ),
)

HEADERS = (
    'Модель',
    'Стара ціна',
    'Нова ціна',
)


class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = headers
        self.result = []
        self.start_time = None
        self.total_time = None

    def load_page(self, page):
        url = f'https://www.copa.com.ua/index.php?route=product/search&search={MANUFACTURER}&sort=p.price&order=DESC&limit=100&page={page}'
        res = self.session.get(url)
        res.raise_for_status()
        return res.content

    def parse_page(self, html):
        soup = bs4.BeautifulSoup(html, 'html.parser')
        cards = soup.select('.product-layout')

        if not cards:
            return False

        for card in cards:
            goods_name_elem = card.select_one('.caption span.h4 a')
            url = goods_name_elem['href']
            price_new_elem = card.select_one('.price .price-new')
            if price_new_elem:
                price_new = price_new_elem.text.strip()
                price_old_elem = card.select_one('.price .price-old')
                if price_old_elem:
                    price_old = price_old_elem.text.strip()
                else:
                    price_old = None
            else:
                price_elem = card.select_one('.price')
                price_new = price_elem.text.strip()
                price_old = None


            additional_info = self.parse_additional_info(url)
            self.result.append(ParseResult(
                price_old=price_old,
                price_new=price_new,
                model=additional_info['model'],
            ))

        return True

    def parse_additional_info(self, url):
        res = self.session.get(url)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.content, 'lxml')

        model = model_elem.text.strip() if (
                model_elem := soup.select_one('div.bg-white.list-info span:-soup-contains("Модель:") + span')) else None

        additional_info = {
            'model': model,
        }
        return additional_info

    def save_results(self):
        with open('copa.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        logger.info('Загрузка страницы...')
        page = 18
        self.start_time = time.time()

        while True:
            logger.info(f'Парсинг страницы {page}...')
            html = self.load_page(page)
            has_next_page = self.parse_page(html)
            logger.info(f'Сохранение результатов страницы {page}...')

            elapsed_time = time.time() - self.start_time
            logger.info(f'Время парсинга текущей страницы: {elapsed_time:.2f} секунд')

            self.save_results()

            if not has_next_page or any(result.price_new == '0 грн.' for result in self.result):
                self.total_time = time.time() - self.start_time
                logger.info(f'Общее время парсинга всех страниц: {self.total_time:.2f} секунд')
                break

            page += 1
            time.sleep(1)

        logger.info('Готово!')


if __name__ == '__main__':
    client = Client()
    client.run()
