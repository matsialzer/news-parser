from parsers.scrapers.utils import save_last_date
from bs4 import BeautifulSoup
from datetime import datetime
from urllib import parse
from typing import List
import requests
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')


encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

BASE_URL = "https://sports.uz/"


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = requests.get(link)
    soup = BeautifulSoup(req.text, 'html.parser')

    # ----  title  ---- //
    title = soup.find("div", class_="news-header")
    post_info["title"] = title.find("h1").text
    # // ----  title  ----

    # ----  main image  ---- //
    main_image = None
    main_img_div = soup.find("img", class_="news-img")
    if main_img_div:
        main_image = main_img_div['src']
    post_info['main_image'] = main_image
    # // ----  main image  ----

    # ----  texts & images  ---- //
    _news_body = soup.find("div", class_="news-body")
    _all_p: object = _news_body.find_all('p')
    text: str = ""
    images = []
    if _all_p:
        for p in _all_p:
            img = p.find('img')
            if img:
                images.append(img['src'])
            text += p.text + '\n'
    post_info['text'] = text
    post_info['images'] = images
    # // ----  texts & images  ----

    # ----  tags  ---- //
    _tags = soup.find("ul", class_="tags").find_all("a")
    if _tags:
        tags = [
            {
                'name': tag.text,
                'url': BASE_URL + encoder_utf_8(tag['href'])
            }
            for tag in _tags
        ]
        post_info['tags'] = tags
    # // ----  tags  ----

    return post_info


# link = "https://sports.uz/news/view/argentina-prezidenti-terma-jamoaning-muvaffaqiyat-sirini-aytdi-14-12-2022"
# link = "https://sports.uz/news/view/yaxshi-oynay-olmasangiz-snayper-sizga-qaratiladi--bir-necha-davlatlardan-aniq-takliflar-bor--lekin---legionerimiz-qaysi-yolni-tanlaydi-13-12-2022"
# link = "https://sports.uz/news/view/bizga-mukofotga-katta-summa-vada-qilishgan-edi-polsha-terma-jamoasida-katta-janjal-chiqdi-13-12-2022"
link = "https://sports.uz/news/view/mourino-afrikalik-futbolchilarning-boshqa-mamlakat-sharafini-himoya-qilishiga-qarshi-%28foto%29-16-12-2022"
# result = get_post_detail(link=link)
# print(result)


def collect_new_links(last_date: datetime) -> List[str]:
    new_last_date = None
    has_next_page = True
    links = []
    months = {
        'Январь': '01',
        'Февраль': '02',
        'Март': '03',
        'Апрель': '04',
        'Май': '05',
        'Июнь': '06',
        'Июль': '07',
        'Август': '08',
        'Сентябрь': '09',
        'Октябрь': '10',
        'Ноябрь': '11',
        'Декабрь': '12'
    }
    page = 1
    flag = True
    while flag:
        req = requests.get(f'https://sports.uz/news/index?page={page}')
        page += 1
        if not has_next_page:
            break
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            articles = soup.find('main', class_='main-content').find('div', class_='news-list').find_all('div', class_='item')
            for article in articles:
                link = 'https://sports.uz/news' + article.find('a').get('href')
                try:
                    i = article.find('div', class_='news-body').find('ul').find('li').text
                    date = i.split(' ')
                    if len(date) == 4:
                        day = date[1]
                        month = months[date[2].replace(',', '').capitalize()]
                        year = datetime.now().strftime('%Y')
                        time = date[3]
                        date = day + '-' + month + '-' + year + ' ' + time
                        date = datetime.strptime(date, '%d-%m-%Y %H:%M')
                    else:
                        day = date[1]
                        month = months[date[1].replace(',', '').capitalize()]
                        year = date[3][:-1]
                        time = date[4]
                        date = day + '-' + month + '-' + year + ' ' + time
                        date = datetime.strptime(date, '%d-%m-%Y %H:%M')
                    if date > last_date:
                        links.append(link)
                        if not new_last_date:
                            new_last_date = last_date
                    else:
                        has_next_page = False
                        break
                except Exception as e:
                    logger.error(f'error in sports new links collector : {e}')
        else:
            break
    if new_last_date:
        save_last_date('goal24', new_last_date.timestamp())
    return links