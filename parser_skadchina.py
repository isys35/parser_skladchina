import requests
from bs4 import BeautifulSoup
from typing import List
import db

HOST = 'https://www.skladchina.biz/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
}


def save_page(response: str, file_name='page.html'):
    """
    Сохранение ответа на завпрос в html файл
    """
    with open(file_name, 'w', encoding='utf-8') as html_file:
        html_file.write(response)


def get_response(url: str) -> str:
    """
    Получение ответа на запрос
    """
    while True:
        try:
            response = requests.get(url, headers=HEADERS)
            break
        except ConnectionError:
            continue
    if response.status_code == 200:
        return response.text
    else:
        print('[ERROR] Response status code: {}'.format(response.status_code))


def parse_rubrics(response: str) -> List[dict]:
    """
    Парсер рубрик из ответа на запрос
    """
    soup = BeautifulSoup(response, 'lxml')
    skladchini_block = soup.find("li", {"id": "skladchiny.46"})
    titles = skladchini_block.select_one('ol.nodeList ').select('h3.nodeTitle')
    rubrics = []
    for title in titles:
        url = HOST + title.select_one('a')['href']
        name_rubric = title.select_one('a')['title']
        rubrics.append({'name': name_rubric, 'url': url})
    return rubrics


def parse_max_page(response: str) -> int:
    soup = BeautifulSoup(response, 'lxml')
    return int(soup.select_one('div.PageNav')['data-last'])


def parse_skladchini(response: str) -> List[dict]:
    """
    Парсер складчин с ответа на запрос
    склачина - {'наименованиее данных':'данные'}
    """
    soup = BeautifulSoup(response, 'lxml')
    list_items = soup.select('.discussionListItem')
    skladchini = []
    for list_item in list_items:
        prefix_link = list_item.select_one('.prefixLink')
        if prefix_link:
            status = prefix_link.text
            name = list_item.select_one('a.PreviewTooltip').text
            url = HOST + list_item.select_one('a.PreviewTooltip')['href']
            date = list_item.select_one('.startDate').select_one('.DateTime').text
            deposit = list_item.select_one('.estcs-shopping-description').select_one('dd').text
            main = list_item.select_one('dl.major').select_one('dd').text
            rezerve = None
            views = list_item.select_one('dl.minor').select_one('dd').text
            skladchini.append({'status': status,
                               'name': name,
                               'url': url,
                               'date': date,
                               'deposit': deposit,
                               'main': main,
                               'rezerve': rezerve,
                               'views': views
                               })
    return skladchini


def parse_skladchina(response: str) -> dict:
    """
    Парсер складчины с ответа на запрос
    склачина - {'наименованиее данных':'данные'}
    """
    soup = BeautifulSoup(response, 'lxml')
    price = soup.select_one('dl.estcs-shopping-info-extra-tabs').select_one('dd').text
    return {'price': price}


def get_rubrics() -> List[dict]:
    """
    Получение рубрик
    """
    response = get_response(HOST)
    rubrics = parse_rubrics(response)
    return rubrics


def get_skladchini(rubric_url: str) -> List[dict]:
    """
    Получение складчин со страници рубрики
    складчина - {'наименованиее данных':'данные'}
    """
    response = get_response(rubric_url)
    max_page = parse_max_page(response)
    skladchini = parse_skladchini(response)
    if max_page > 1:
        for page in range(2, max_page + 1):
            print(f'[INFO] Страница {page}/{max_page}')
            url_page = rubric_url + f'page-{page}'
            response_page = get_response(url_page)
            skladchini_from_page = parse_skladchini(response_page)
            skladchini.extend(skladchini_from_page)
    return skladchini


def get_skladchina(skladchina_url: str) -> dict:
    """
    Получение данных со страницы складчины
    склачина - {'наименованиее данных':'данные'}
    """
    response = get_response(skladchina_url)
    skladchina = parse_skladchina(response)
    return skladchina


def parser():
    """
    ПАРСЕР
    """
    rubrics = get_rubrics()
    for rubric in rubrics:
        db.create_file(rubric['name'] + '.xlsx')
        skladchini = get_skladchini(rubric['url'])
        for index, skladchina in enumerate(skladchini):
            skladchina_detail = get_skladchina(skladchina['url'])
            skladchina['rubric'] = rubric['name']
            skladchina_full = {**skladchina, **skladchina_detail}
            print('{} {}/{}'.format(rubric['name'], index, len(skladchini)))
            db.add_skladchina(skladchina_full, rubric['name'] + '.xlsx')


if __name__ == '__main__':
    parser()
