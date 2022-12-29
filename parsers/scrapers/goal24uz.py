from datetime import datetime, timedelta
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup

from parsers.models import NewsLinks
from parsers.scrapers.utils import save_last_date

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

BASE_URL = "https://goal24.uz/"


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = requests.get(link)
    soup = BeautifulSoup(req.text, 'html.parser')

    # ----  title  ---- //
    title = soup.find("h1", class_="post-title")
    post_info["title"] = title.find("span").text
    # // ----  title  ----

    # ----  main image  ---- //
    main_image = None
    main_img_div = soup.find("div", class_="fstory")
    if main_img_div:
        main_image = main_img_div.find("img")["src"]
    post_info['main_image'] = f"{BASE_URL}{main_image}"
    # // ----  main image  ----

    # ----  texts & images  ---- //
    _news_body = soup.find("div", class_="fstory")

    _all_texts: object = _news_body
    _all_images = _news_body.find_all("img")[1:]

    text: str = ""
    images = []
    if _all_texts:
        for p in _all_texts.strings:
            text += p.strip()

    if _all_images:
        for image in _all_images:
            if image['data-src'].startswith("https://"):
                images.append(image["data-src"])
            else:
                images.append(f'{BASE_URL}{image["data-src"]}')
    post_info['text'] = text
    post_info['images'] = images
    # // ----  texts & images  ----

    # ---- videos ---- //
    videos = []
    _all_videos = _news_body.find_all("iframe")
    if _all_videos:
        for video in _all_videos:
            videos.append(video["src"])
    post_info["videos"] = videos

    return post_info


# link = "https://goal24.uz/32805-transfer-yangliklari-man-utd-kozi-portugalyalik-mojizada-arsenalning-kozi-gollandya-terma-jamoasi-himoyachisida.html"
# link = "https://goal24.uz/32897-argentina-qatardagi-jahon-chempionatining-ilk-finalchisi.html"
# link = "https://goal24.uz/5294-agar-onam-bolmaganida-futbolni-aniq-tashlab-ketardim-anxel-di-mariyaning-tasirli-hikoyasi.html"
# link = "https://goal24.uz/32287-jahon-chempionatidagi-barcha-jarohatlar-frantsiyaning-minus-besh-yulduzi-va-manet-fojiasi.html"
# link = "https://goal24.uz/32178-chempionlar-ligasi-guruh-bosqichining-eng-yaxshi-goli-aniqlandi.html"
link = "https://goal24.uz/5358-38-yildan-beri-davom-etayotgan-koma-fransiyalik-sobiq-futbolchi-va-unga-sodiq-qolayotgan-ayol-haqida-hikoya.html"
# result = get_post_detail(link=link)
# print(result)


def collect_new_links(last_date: datetime) -> List[str]:
    new_last_date = None
    has_next_page = True
    links = []
    for i in range(1, 3500):
        if not has_next_page:
            break
        req = requests.get(f'https://goal24.uz/lastnews/page/{i}/')
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            articles = soup.find_all('div', class_='shortstory2')
            for article in articles:
                date = article.find('div', class_='sdate').text.split('|')[0].strip()
                link = article.find('a').get('href')
                if 'Bugun' in date or 'Kecha' in date:
                    time = date.split(',')[1]
                    if 'Bugun' in date:
                        date = datetime.now().strftime('%d-%m-%Y')
                    else:
                        date = (datetime.now() - timedelta(days=1)).strftime('%d-%m-%Y')
                    date = date + ' ' + time
                else:
                    day = date.split(',')[0]
                    time = date.split(',')[1]
                    date = day + ' ' + time
                date_in_datatime = datetime.strptime(date, '%d-%m-%Y %H:%M')
                if date_in_datatime > last_date:
                    links.append(link)
                    if not new_last_date:
                        new_last_date = last_date
                else:
                    has_next_page = False
                    break

    if new_last_date:
        save_last_date('goal24', new_last_date.timestamp())
    return links