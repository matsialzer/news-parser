import json
import os, sys, django
import re
import requests

# ---------  Setup django  //  --------------
path_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(path_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
# ---------  //  Setup django  --------------

from parsers.tasks import (
    bbc_parser, bugun_parser, get_last_date, daryo_parser, gazeta_parser, 
    kun_parser, olamsport_parser, qalampir_parser, 
    uza_parser, championat_parser, aniq_parser, 
    zamin_parser, sputniknews_parser, goal24_parser,
    sports_parser
)
from django.conf import settings
from datetime import datetime, date
from random import choice

seconds = [0.5, 0.6, 0.7, 0.8, 0.9, 1]

# print(get_last_date('championat'))

def write_new_date(site, datetuple, link=None):
    path = f"{settings.BASE_DIR}/parsers/scrapers/data/{site}.txt"
    with open(path, 'w') as f:
        d_time = datetime(*datetuple)
        if link:
            data = f'{str(d_time.timestamp())},{link}'
        else:
            data = str(d_time.timestamp())
        f.write(data)

# link = "https://championat.asia/oz/news/instagram-messi-ronalduni-maglub-etdi-navbat-tuhumga"


# last_link = 'https://www.bbc.com/uzbek/uzbekistan-63906630'
# write_new_date('bbc', (2022, 12, 7, 7, 0), last_link)
# bbc_parser.apply_async(args=(False, last_link))


# bugun_link = 'https://bugun.uz/2022/12/27/ozbekistonda-1-yanvardan-qonunchilikda-nimalar-ozgaradi/'
# bugun_link = 'https://olamsport.com/oz/news/nemkov-romero-jangi-nomalum-muddatga-qoldirildi'
# write_new_date('daryo', (2022, 12, 7, 7, 0))
# link = 'https://daryo.uz/2022/12/28/aqsh-kiyevni-qollab-quvvatlashdan-toxtasagina-urush-tugaydi-orban'
# link = 'https://www.gazeta.uz/uz/2022/12/28/river/'
# link = 'https://kun.uz/news/2022/12/26/bolalar-ombudsmani-samarqanddagi-dok-1maks-preparati-bilan-bogliq-holatni-organdi'
# link = 'https://kun.uz/news/2022/12/26/tora-bobolov-surxondaryo-viloyati-hokimi-lavozimidan-ozod-etildi'
# link = 'https://qalampir.uz/uz/news/yer-usti-metro-liniyasi-fak-at-bugun-kech-ish-boshladi-74732'
# link = 'https://qalampir.uz/uz/news/dunening-eng-keksa-toshbak-asi-190-yeshini-nishonladi-74710'
# link = 'https://uza.uz/uz/posts/ozbekiston-respublikasi-prezidenti-mdhning-norasmiy-sammitida-ishtirok-etdi_439027'
# link = 'https://uza.uz/uz/posts/vazirlar-mahkamasi-izhro-etuvchi-tuzilmasini-ozgartirishdan-maqsad-nima_439246'
# link = 'https://uza.uz/uz/posts/adliya-aralashuvi-bilan-xodimlar-ishiga-tiklandi_439678'
# link = 'https://zamin.uz/uz/dunyo/110510-rossiya-gazidan-voz-kechgan-germaniya-tuzoqqa-tushib-qoldi.html'
# link = 'https://zamin.uz/uz/dunyo/110559-sobiq-aqsh-razvedka-xodimi-rossiyadan-nimani-organish-kerakligini-aytdi.html'
# link = 'https://sputniknews-uz.com/20221228/bayram-kunlari-elektr-va-gaz-boyicha-qarzdorlik-yuzaga-kelsa-aholi-tarmoqdan-uzilmaydi-31099812.html'
# link = 'https://sputniknews-uz.com/20221228/ozbekiston-va-qirgiziston-chegara-demarkatsiyasini-yakunlash-uchun-hujjatlarni-tayyorladi-31097489.html'
# link = 'https://aniq.uz/yangiliklar/uz-vatanidan-nafratlangan-sotqinlar-umrining-oxirigacha-rossiyaga-qaytarilmasligi-kerak-medvedev'
# link = 'https://aniq.uz/yangiliklar/germaniya-tashqi-ishlar-vaziri-rossiya-bilan-munosabatlarni-saqlab-qolishning-iloji-yuqligini-takidladi'
# link = 'https://goal24.uz/33012-psj-fred-bilan-shartnoma-imzolashi-mumkin.html'
# link = 'https://goal24.uz/33010-barselona-yangi-sardorni-tanladi.html'
# link = 'https://sports.uz/news/view/metallurg-bosniyalik-legioneri-bilan-yana-bir-yillik-shartnoma-imzoladi-28-12-2022'
# link = 'https://sports.uz/news/view/paxtakor-tursunov-bilan-shartnomani-uzaytirdi--28-12-2022'
# link = 'https://championat.asia/oz/news/aplning-3-ta-top-klubi-pikfordga-koz-tikdi'
# link = 'https://championat.asia/oz/news/kulusevski-shveciyada-yil-futbolchisi'
# link = 'https://olamsport.com/oz/news/wboning-yangilangan-reytingida-shohjahon-ergashev-yuqoriladi-poster-4'
# link = 'https://olamsport.com/oz/news/jervonta-devis-jangiga-ikki-hafta-qolganda-qamoqqa-olindi'
# link = 'https://bugun.uz/2022/12/28/xorazmda-oqituvchi-xtv-ustamasi-uchun-otkazilgan-imtihonda-100-foizlik-natija-qayd-etdi/'
# link = 'https://bugun.uz/2022/12/28/samarqandda-500-ga-yaqin-oquvchisi-otmga-kirgan-oqituvchi-xtv-ustamasi-imtihonida-100-foizlik-natija-qayd-etdi/'
# link = 'https://www.bbc.com/uzbek/world-60872788'
# link = 'https://www.bbc.com/uzbek/world-60899262'
link = 'https://kun.uz/news/2022/12/26/bolalar-ombudsmani-samarqanddagi-dok-1maks-preparati-bilan-bogliq-holatni-organdi'
link = 'https://kun.uz/news/2022/12/27/18-bolani-oldirgan-beparvolik-davlat-retsepsiz-dori-savdosini-darhol-toxtatishi-kerak'
kun_parser.apply_async(args=(False, link))


# from bs4 import BeautifulSoup

# req = requests.get(link)

# soup = BeautifulSoup(req.content, 'html.parser')
# tag_block = soup.find_all('a')
# print(tag_block)

# dt = datetime.fromtimestamp(639465980.0)
# dt2 = datetime.fromtimestamp(639742030.0)
# dt2 = datetime.fromtimestamp(12812690200.0)
# dt2 = datetime.fromtimestamp(1281268990)
# dt2 = datetime.fromtimestamp(1281119650)
# dt2 = datetime.fromtimestamp(64102322)
# print(dt)
# print(dt2)

# dt = date(2022, 12, 28)
# print(dt)
# print(dt.strftime)

# next_page = soup.find('span', visibility='ALL')
# if next_page:
#     a = next_page.find('a')



# link = 'https://sputniknews-uz.com/20221227/tojikistondagi-zilzila-kuchi-ozbekistonda-sezildi-31063084.html'
# time = ' asda 08:18  '

# date_regex = '([\d]{8})/'
# date_res = re.search(date_regex, link).groups()

# time_regex = '([\d]{2}):([\d]{2})'
# time_regex = '([0-1]?[0-9]|2[0-3]):[0-5][0-9]'

# time_res = re.search(time_regex, time).groups()

# print(date_res, len(time))

# str_dtime = """9834   
#                      3                

#  Muallif:
# Alisher Ostonov 
#                     27 dek 2021, 12:07"""
# time_regex = '([\d]{2}) ([\w]{3}) ([\d]{4})'
# _res_time = re.search(time_regex, str_dtime).groups()
# print(_res_time)

# championat_parser.apply_async(args=(False, link,))


# r'/(\d{4})/(\d{1,2})/(\d{1,2})/'
# re.search("([0-9]{2}\-[0-9]{2}\-[0-9]{4})", fileName)


def extract_dates(txt: str):
    dtime_matcher = '([0-9]{2}\.[0-9]{2}\.[0-9]{4})'
    res = re.search(dtime_matcher, txt)
    print(res.groups())

# string_date = "Kiritildi: 00:49, 27.12.2022. O'qildi: 8 marta. Fikrlar soni: 0 ta."

# string_date = '27.12.2022'
# print(type(string_date))

# date_object = datetime.strptime(string_date, '%d.%m.%Y').date()

# print(date_object)

# print(type(date_object))

# from email import utils
# str_d_time = 'Thu Jun 07 01:13:25 +0000 2018'
# date = utils.parsedate_to_datetime(str_d_time)
# print(date)

# s = 'Thu Jun 07 01:13:25 +0000 2018'
# from datetime import datetime
# d = datetime.strptime(s,'%a %b %d %H:%M:%S %z %Y')
# print(d)

# page = 2
# next_page_url = f"https://qalampir.uz/uz/news/latest/load-more?page={page}"
# req = requests.get(next_page_url)
# print(type(json.loads(req.content)))
# print(json.loads(req.content['data']))


# print(choice(seconds))

# write_new_date('uza', 2022, 12, 26, 17, 33)

# uza_parser.apply_async(args=(True,))

# qalampir_parser.apply_async(args=(True,))

# kun_parser.apply_async(args=(True,))

# gazeta_parser.apply_async(args=(True,))
#27 ta


# daryo_parser.apply_async(args=(True,))

# today = datetime.today()
# print(today)
# timestamp = today.timestamp()
# print(timestamp)
# qwe = datetime.fromtimestamp(timestamp)
# print(qwe)


# # link = 'https://kun.uz/news/2022/12/25/2023-yil-anonsi-15-karra-kop-elektr-va-eski-yangi-vazirliklar-hafta-dayjesti'

# try:
#     f = open(path)
#     print(f.read())
# except:
#     with open(path, 'w') as f:
#         f.write('')


