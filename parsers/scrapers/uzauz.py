from datetime import datetime
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup

from parsers.models import NewsLinks
from parsers.scrapers.utils import save_last_date

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

BASE_URL = "https://uza.uz/uz"


def get_post_detail(link: str) -> dict:
    post_info: dict = {}
    try:
        req = requests.get(link)
        soup = BeautifulSoup(req.text, 'html.parser')

        # ----  title  ---- //
        title = soup.find("div", class_="news-top-head__title")
        post_info["title"] = title.text
        # // ----  title  ----

        # ---- main image --- //
        main_image = None
        main_image_div = soup.find("div", class_="news-top-head__content")
        if main_image_div:
            main_image = main_image_div.find('img')['src']
        post_info["main_image"] = main_image
        # // ---- main image ----

        _single_content = soup.find('div', class_='content-block')

        # ----  summary  ---- //
        _summary = _single_content.find('h4')
        summary = None
        if _summary:
            summary = _summary.text
        post_info['summary'] = summary
        # // ----  summary  ----

        # ---- texts and images ---- //
        images = []
        figures = soup.find_all('figure', class_='image')
        for fig in figures:
            try:
                img = fig.find('img')
                if img:
                    images.append(img['src'])
            except Exception as e:
                pass

        text = ""
        _all_p = _single_content.find_all('p')
        if _all_p:
            for p in _all_p:
                text += p.text + '\n'

        post_info['text'] = text
        post_info['images'] = images
        # // ----  texts & images  ----

        # ----  video  ---- //
        try:
            _pre = _single_content.find('pre')
            _code = _pre.find('code')
            _iframe_str = _code.text
            link_start = _iframe_str.find('https://www.youtube.com/')
            post_info["video"] = _iframe_str[link_start:_iframe_str.find(' ', link_start)]
        except:
            pass

        # // ----  video  ----

        # --- tags ---- //
        tags = []
        try:
            _tags_div = soup.find("div", class_="news-tags")
            _tags = _tags_div.find_all("a", class_="news-tags__item")  # TODO
            if _tags:
                for tag in _tags:
                    tags.append(
                        {
                            'name': tag.text,
                            'url': BASE_URL + encoder_utf_8(tag['href'])
                        }
                    )
        except Exception as e:
            pass
        post_info['tags'] = tags
        # // ----  tags  ----
    except Exception as e:
        post_info['errors'] = e
    return post_info


link = "https://uza.uz/uz/posts/iqtisodiyot-va-boshqaruvdagi-islohotlarning-borishi-yuzasidan-fikr-almashildi_436197"
# link = "https://uza.uz/uz/posts/tezhamkorlik-va-samaradorlik-elektr-taminoti-barqarorligida-muhim-omil-video_435765"
# result = get_post_detail(link=link)
# print(result)


def collect_new_links(last_date: datetime=None) -> List[str]:
    has_next_page = True
    count = 0
    links = []
    new_last_date = None
    for i in range(1, 3):
        if not has_next_page:
            break
        api = f'https://api.uza.uz/api/v1/posts?page={i}'
        req = requests.get(api)
        if req.status_code == 200:
            data = req.json()['data']
            for item in data:
                date = item['publish_time']
                link ='https://uza.uz/uz/posts/' + item['slug']
                date_in_datatime = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                yield (link, date_in_datatime)
                    # if date_in_datatime > last_date:
                    #     links.append(link)
                    #     count += 1
                    #     if not new_last_date:
                    #         new_last_date = date_in_datatime
                    # else:
                    #     has_next_page = False
                    #     break
        break
    if new_last_date:
        save_last_date('uza', new_last_date.timestamp())
    return links

