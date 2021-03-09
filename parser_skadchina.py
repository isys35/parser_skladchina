from bs4 import BeautifulSoup
from typing import List
import db
from requests import Session
from urllib.parse import quote
from datetime import datetime
import re

HOST = 'https://www.skladchina.biz/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
}
HEADERS_LOGIN = {
    'Host': 'www.skladchina.biz',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Content-Length': '93',
    'Origin': 'https://www.skladchina.biz',
    'Cookie': '_ym_uid=1614277842861231321',
    'Connection': 'keep-alive',
    'Referer': 'https://www.skladchina.biz/',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers'
}

HEADERS_SIGN_UP = {
    'Host': 'www.skladchina.biz',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': '*/*',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Length': '67',
    'Origin': 'https://www.skladchina.biz',
    'Connection': 'keep-alive',
    'TE': 'Trailers'
}

HEADERS_REKVIZIT = {
    'Host': 'www.skladchina.biz',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers'
}

RU_MONTH_VALUES = {
    'янв': 1,
    'фев': 2,
    'мар': 3,
    'апр': 4,
    'май': 5,
    'июн': 6,
    'июл': 7,
    'авг': 8,
    'сен': 9,
    'окт': 10,
    'ноя': 11,
    'дек': 12,
}

session = Session()


def int_value_from_ru_month(date_str):
    for k, v in RU_MONTH_VALUES.items():
        date_str = date_str.replace(k, str(v))
    return date_str


def login(email, password):
    url = 'https://www.skladchina.biz/login/login'
    data = 'login={}&password={}&remember=1&cookie_check=1&redirect=%2F&_xfToken='
    data = data.format(quote(email), quote(password))
    session.post(url, data=data, headers=HEADERS_LOGIN)


def sign_up(url, token, referer):
    """
    Запись на складчину
    """
    headers = HEADERS_SIGN_UP
    headers['Referer'] = referer
    session.headers.update(headers)
    data = '_xfToken={}'.format(token)
    response = session.post(url, data=data)
    return response.text


def leave(url, token, referer):
    """
    Отписка от складчины
    """
    sign_up(url, token, referer)


def parse_rekvizit_url(response: str) -> str or None:
    """
    Парсинг ссылки на реквизиты
    """
    soup = BeautifulSoup(response, 'lxml')
    btn = soup.select_one('#LeaveButton')
    if not btn:
        return
    if not btn.select_one('a'):
        return
    return HOST + btn.select_one('a')['href']


def parse_leave_url(response: str) -> str:
    soup = BeautifulSoup(response, 'lxml')
    btn = soup.select_one('a.button-new-primary.estcs-button')
    return HOST + btn['href']


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
            response = session.get(url)
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
    page_nav = soup.select_one('div.PageNav')
    if page_nav:
        return int(soup.select_one('div.PageNav')['data-last'])
    else:
        return 1


def parse_event(response: str) -> dict:
    """
    Парсинг событий
    :return {'count' : кол-во участвующих, 'date': дата первого события}
    """
    soup = BeautifulSoup(response, 'lxml')
    scroller = soup.select_one('.alerts.alertsScroller')
    count = 0
    for li in scroller.select('li'):
        if re.search('участвует в складчине в резервном списке', str(li)):
            continue
        if re.search('участвует в складчине', str(li)):
            count += 1
    if scroller.select('li'):
        try:
            first_date = scroller.select('li')[-1].select_one('.DateTime')['title']
        except KeyError:
            first_date = scroller.select('li')[-1].select_one('.DateTime')['data-datestring']
        first_date = transform_date(first_date)
        return {'count': count, 'date': first_date}
    else:
        return {'count': 0, 'date': datetime.now()}


def transform_date(init_date: str) -> datetime:
    date_str = int_value_from_ru_month(init_date)
    if 'в' in date_str:
        date = datetime.strptime(date_str, '%d %m %Y в %H:%M')
    else:
        date = datetime.strptime(date_str, '%d %m %Y')
    return date


def parse_skladchini(response: str) -> List[dict]:
    """
    Парсер складчин с ответа на запрос
    склачина - {'наименованиее данных':'данные'}
    """
    soup = BeautifulSoup(response, 'lxml')
    list_items = soup.select('.discussionListItem')
    skladchini = []
    for list_item in list_items:
        if 'sticky' in list_item.attrs['class']:
            continue
        prefix_link = list_item.select_one('.prefixLink')
        if prefix_link:
            status = prefix_link.text
            name = list_item.select_one('a.PreviewTooltip').text
            url = HOST + list_item.select_one('a.PreviewTooltip')['href']
            date = list_item.select_one('.startDate').select_one('.DateTime').text
            date = transform_date(date)
            deposit = list_item.select_one('.estcs-shopping-description').select_one('dd').text
            main = list_item.select_one('dl.major').select_one('dd').text
            views = list_item.select_one('dl.minor').select_one('dd').text
            skladchini.append({'status': status,
                               'name': name,
                               'url': url,
                               'date': date,
                               'deposit': deposit,
                               'main': main,
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
    hash_tags = [el.text for el in soup.select('.link.tag')]
    re_search_id = re.search(r'showImportantLogs\((\d+)\);', str(soup.select_one('#important-logs')))
    id_skladchina = re_search_id.group(1)
    return {'price': price, 'hash_tags': hash_tags, 'id': id_skladchina}


def get_rubrics() -> List[dict]:
    """
    Получение рубрик
    """
    response = get_response(HOST)
    rubrics = parse_rubrics(response)
    return rubrics


def get_skladchini(rubric_url: str, first_page=1, max_page=None, sort=False) -> List[dict]:
    """
    Получение складчин со страници рубрики
    складчина - {'наименованиее данных':'данные'}
    """
    if sort:
        response = get_response(rubric_url + '?order=post_date')
    else:
        response = get_response(rubric_url)
    parsed_max_page = parse_max_page(response)
    if not max_page:
        max_page = parsed_max_page
    else:
        if parsed_max_page < max_page:
            max_page = parsed_max_page
    if first_page == 1:
        skladchini = parse_skladchini(response)
        print(f'[INFO] Страница 1/{max_page}')
        yield skladchini
    if max_page > 1:
        for page in range(first_page, max_page + 1):
            if page == 1:
                continue
            print(f'[INFO] Страница {page}/{max_page}')
            if sort:
                url_page = rubric_url + f'page-{page}?order=post_date'
            else:
                url_page = rubric_url + f'page-{page}'
            response_page = get_response(url_page)
            skladchini_from_page = parse_skladchini(response_page)
            yield skladchini_from_page


def get_skladchina(skladchina_url: str) -> dict:
    """
    Получение данных со страницы складчины
    склачина - {'наименованиее данных':'данные'}
    """
    response = get_response(skladchina_url)
    skladchina = parse_skladchina(response)
    event_url = 'https://www.skladchina.biz/threads/showLog?shopping_id={}&important=0'.format(skladchina['id'])
    response_events = get_response(event_url)
    event = parse_event(response_events)
    skladchina['event'] = event
    return skladchina


def get_rubric_name(rubric_url: str) -> str:
    response = get_response(rubric_url)
    soup = BeautifulSoup(response, 'lxml')
    return soup.select_one('h1').text


def parser(url_rubric, rubric_name, excel, first_page=1, max_page=None, sort=False, delta_days=None):
    skladchini = get_skladchini(url_rubric, first_page, max_page, sort)
    for skladchini_from_page in skladchini:
        for index, skladchina in enumerate(skladchini_from_page):
            skladchina_detail = get_skladchina(skladchina['url'])
            skladchina['rubric'] = rubric_name
            skladchina_full = {**skladchina, **skladchina_detail}
            if delta_days:
                if (datetime.now() - skladchina_full['date']).days > delta_days:
                    excel.save()
                    return
            print('{} {}/{}'.format(rubric_name, index, len(skladchini_from_page)))
            excel.add_skladchina(skladchina_full)
        excel.save()


def parser_1():
    """
    Парсер 1-й режим:
    парсер всего форума
    """
    excel = db.Excel()
    rubrics = get_rubrics()
    for rubric in rubrics:
        excel.file_name = rubric['name'] + '.xlsx'
        excel.create_file()
        parser(rubric['url'], rubric['name'], excel=excel)


def parser_2():
    """
    Парсер 2-й режим:
    парсер одной рубрики по ссылке с сортировкой по дате и ограницением по страницам
    """
    url_rubric = input('Введите url рубрики: ')
    excel = db.Excel()
    rubric_name = get_rubric_name(url_rubric)
    excel.file_name = rubric_name + '.xlsx'
    excel.create_file()
    parser(url_rubric, rubric_name, excel=excel)


def parser_3():
    """
    Парсер 3-й режим:
    парсер одной рубрики по ссылке с сортировкой по дате и ограницением по страницам
    """
    url_rubric = input('Введите url рубрики: ')
    max_page = int(input('Введите максимальное кол-во страниц: '))
    rubric_name = get_rubric_name(url_rubric)
    excel = db.Excel()
    excel.file_name = f'{rubric_name} 1-{max_page}.xlsx'
    excel.create_file()
    parser(url_rubric, rubric_name, max_page=max_page, sort=True, excel=excel)


def parser_4():
    """
    Парсер 4-й режим:
    парсер одной рубрики по ссылке с сортировкой
    по дате и по определённому диапозону страниц
    """
    url_rubric = input('Введите url рубрики: ')
    first_page = int(input('Введите первую страницу: '))
    last_page = int(input('Введите последнюю страницу: '))
    rubric_name = get_rubric_name(url_rubric)
    excel = db.Excel()
    excel.file_name = f'{rubric_name} {first_page}-{last_page}.xlsx'
    excel.create_file()
    parser(url_rubric, rubric_name, first_page=first_page, max_page=last_page, sort=True, excel=excel)


def parser_5(delta_days):
    """
    Парсер 5-й режим:
    парсер всего форума по диапозону времени
    """
    excel = db.Excel()
    rubrics = get_rubrics()
    for rubric in rubrics:
        excel.file_name = rubric['name'] + f'_{delta_days}_days.xlsx'
        excel.create_file()
        parser(rubric['url'], rubric['name'], excel=excel, sort=True, delta_days=delta_days)


def start():
    email = input('Введите email: ')
    password = input('Введите password: ')
    login(email, password)
    info = """Режимы работы:
    1 - парсер всего форума
    2 - парсер одной рубрики по ссылке
    3 - парсер одной рубрики по ссылке с сортировкой 
        по дате и ограницением по страницам
    4 - парсер одной рубрики по ссылке с сортировкой 
        по дате и по определённому диапозону страниц
    5 - парсер всего форума за период вермени"""
    additional_mod_info = """   Доп. Настройка:
        1 - Пол года 
        2 - Месяц
        3 - Неделя"""
    print(info)
    mode = input('Введите режим работы (1/2/3/4/5): ')
    if int(mode) == 1:
        parser_1()
    elif int(mode) == 2:
        parser_2()
    elif int(mode) == 3:
        parser_3()
    elif int(mode) == 4:
        parser_4()
    elif int(mode) == 5:
        print(additional_mod_info)
        additional_mod = input('Доп. настройка(1/2/3):')
        if int(additional_mod) == 1:
            parser_5(182)
        elif int(additional_mod) == 2:
            parser_5(30)
        elif int(additional_mod) == 3:
            parser_5(7)


if __name__ == '__main__':
    start()

