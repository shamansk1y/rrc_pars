import bs4
import logging
import csv
import requests
from fake_useragent import UserAgent
import collections
import time


MANUFACTURER = 'joma'

logger = logging.getLogger('soccer_shop')
logging.basicConfig(level=logging.INFO)

ua = UserAgent()
headers = {'User-Agent': ua.random}
ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'model',
        'price_old',
        'price_new',
        'availability',
    ),
)

HEADERS = (
    'Модель',
    'Стара ціна',
    'Нова ціна',
    'Наявність',
)

class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = headers
        self.result = []
        self.start_time = None
        self.total_time = None

    def load_page(self, page):
        url = f'https://soccer-shop.com.ua/ua/m9-{MANUFACTURER}/sort/price/sortord/d/page/{page}'
        res = self.session.get(url)
        res.raise_for_status()
        return res.content

    def parse_page(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        products = soup.select('.prod')[:59]
        if not products:
            return False


        for product in products:
            price_old_element = product.select_one('.price.old .int')
            price_old = price_old_element.text.strip() if price_old_element else ""
            price_new_element = product.select_one('.price.sale .int')
            price_new = price_new_element.text.strip() if price_new_element else ""
            model_el = product.select_one('.products-model span')
            model = model_el.text.strip() if model_el else ""
            availability_el = product.select_one('.products-quantity.instock')
            availability = availability_el.text.strip() if availability_el else ""

            self.result.append(ParseResult(
                model=model,
                price_old=price_old,
                price_new=price_new,
                availability=availability,
            ))

        return True

    def save_results(self):
        with open('soccer.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        logger.info('Загрузка страницы...')
        page = 1
        self.start_time = time.time()

        while True:
            logger.info(f'Парсинг страницы {page}...')
            html = self.load_page(page)
            has_next_page = self.parse_page(html)
            logger.info(f'Сохранение результатов страницы {page}...')

            # Засекаем время отработки и выводим в терминал
            elapsed_time = time.time() - self.start_time
            logger.info(f'Время парсинга текущей страницы: {elapsed_time:.2f} секунд')

            self.save_results()

            if not has_next_page or any(result.availability == 'під замовлення' for result in self.result):
                self.total_time = time.time() - self.start_time
                logger.info(f'Общее время парсинга всех страниц: {self.total_time:.2f} секунд')
                break

            page += 1
            time.sleep(1)
        logger.info('Готово!')


if __name__ == '__main__':
    client = Client()
    client.run()
