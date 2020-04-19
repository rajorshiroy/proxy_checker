import requests


def get_ip():
    proxy = {
        'http': 'http://kevinxq651:s4vKN8JbHLW0xRYY_country-Greece_session-FMMKprs@s2.kochclub.xyz:31112',
        'https': 'https://kevinxq651:s4vKN8JbHLW0xRYY_country-Greece_session-FMMKprs@s2.kochclub.xyz:31112',
    }
    resp = requests.get('http://httpbin.org/ip', proxies=proxy)
    print(resp.json()['origin'])


for _ in range(10):
    get_ip()
