import json
import time
import requests
from threading import Thread, Lock
from requests.exceptions import ProxyError, SSLError


class Proxy:
    def __init__(self):
        self.raw_proxies = None
        self.proxy_stack = []
        self.found_ips = []
        self.verified_proxies = []
        self.status = {
            'checked': 0,
            'unique': 0,
            'duplicate': 0,
            'failed': 0
        }
        self.status_update_lock = Lock()
        self.get_proxy_lock = Lock()
        self.add_verified_proxy_lock = Lock()
        self.get_json()

    def get_json(self):
        with open('proxies.json') as f:
            self.raw_proxies = json.loads(f.read())

    def verify_proxy(self, proxy: str):
        self.status['checked'] += 1
        username, password, ip, port = proxy.split(':')

        proxy_dict = {
            'http': f'http://{username}:{password}@{ip}:{port}',
            'https': f'https://{username}:{password}@{ip}:{port}',
        }
        try:
            resp = requests.get('http://httpbin.org/ip', proxies=proxy_dict)
            origin = resp.json()['origin']
        except:
            with self.status_update_lock:
                self.status['failed'] += 1
            return None

        if origin in self.found_ips:
            with self.status_update_lock:
                self.status['duplicate'] += 1
            return None
        else:
            with self.status_update_lock:
                self.status['unique'] += 1
                self.found_ips.append(origin)
            return {
                'proxy': f'{username}:{password}@{ip}:{port}',
                'proxy_dict': proxy_dict,
                'ip_footprint': origin
            }

    def verify_proxies(self):
        while True:
            proxy = self.get_proxy()
            if proxy:
                verified = self.verify_proxy(proxy)
                if verified:
                    with self.add_verified_proxy_lock:
                        self.verified_proxies.append(verified)
            else:
                break

    def display_result(self):
        while True:
            # if (self.status['checked'] % 100 == 0 and self.status['checked'] != 0) or self.status['checked'] == 1000:
            print(f'checked: {self.status["checked"]}')
            print(f'unique: {self.status["unique"]}')
            print(f'duplicate: {self.status["duplicate"]}')
            print(f'failed: {self.status["failed"]}')
            print('-' * 40)
            time.sleep(5)

            if self.status['checked'] == 1000:
                break

    def get_proxy(self):
        with self.get_proxy_lock:
            try:
                return self.proxy_stack.pop()
            except:
                return None

    def reset_data(self):
        self.proxy_stack = []
        self.verified_proxies = []
        # self.status = {
        #     'checked': 0,
        #     'unique': 0,
        #     'duplicate': 0,
        #     'failed': 0
        # }


if __name__ == '__main__':
    result = {}
    proxy_checker = Proxy()

    for location, proxies in proxy_checker.raw_proxies.items():
        display_thread = Thread(target=proxy_checker.display_result)
        display_thread.start()

        proxy_checker.proxy_stack = proxies
        check_threads = [Thread(target=proxy_checker.verify_proxies) for _ in range(200)]
        for t in check_threads:
            t.start()
        for t in check_threads:
            t.join()
        result[location] = {
            'status': proxy_checker.status,
            'proxies': proxy_checker.verified_proxies
        }

        display_thread.join()
        proxy_checker.reset_data()
        with open(f'results/{location}.json', 'w') as f:
            f.write(json.dumps({
                'status': proxy_checker.status,
                'proxies': proxy_checker.verified_proxies
            }, indent=2))
    with open('verified_proxies.json', 'w') as f:
        f.write(json.dumps(result, indent=2))
