import requests
from bs4 import BeautifulSoup
from decimal import Decimal

def today_USD_rate():
    exchange_rate = -1
    page = requests.get('https://rate.bot.com.tw/xrt?Lang=zh-TW')
    soup = BeautifulSoup(page.content, 'html.parser')
    trs = soup.find_all('tr')

    for currency in trs:
        if 'USD' in currency.get_text():
            trs = currency
            break

    try:
        tds = trs.find_all('td', class_="text-right display_none_print_show print_width")
    except:
        return exchange_rate

    n = len(tds)

    try:
        exchange_rate = (Decimal(tds[n-1].get_text())+Decimal(tds[n-2].get_text()))/2
    except:
        return exchange_rate

    return exchange_rate

def last_day_USD_rate():
    exchange_rate = -1
    page = requests.get('https://rate.bot.com.tw/xrt/all/day')
    soup = BeautifulSoup(page.content, 'html.parser')
    trs = soup.find_all('tr')

    for currency in trs:
        if 'USD' in currency.get_text():
            trs = currency
            break
    
    try:
        tds = trs.find_all('td', class_="phone-small-font text-right rate-content-sight print_table-cell")
    except:
        return exchange_rate

    n = len(tds)

    try:
        exchange_rate = (Decimal(tds[n-1].get_text())+Decimal(tds[n-2].get_text()))/2
    except:
        return exchange_rate

    return exchange_rate

def last_business_day():
    page = requests.get('https://rate.bot.com.tw/xrt/all/day')
    soup = BeautifulSoup(page.content, 'html.parser')
    last = soup.find('p', class_='text-info').get_text()
    last = last.strip().split(' ')
    return last[1]

def scraping_time():
    page = requests.get('https://rate.bot.com.tw/xrt?Lang=zh-TW')
    soup = BeautifulSoup(page.content, 'html.parser')
    last = soup.find('p', class_='text-info').get_text()
    last = last.strip().split(' ')
    return last[1]

if __name__ == "__main__":
    pass
    print(scraping_time())



