# -*- coding: UTF-8 –*-
"""
@Author: LennonChin
@Contact: i@coderap.com
@Date: 2021-10-19
"""

import sys
import os
import random
import datetime
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse


class Utils:

    @staticmethod
    def time_title(message):
        return "[{}] {}".format(datetime.datetime.now().strftime('%H:%M:%S'), message)

    @staticmethod
    def log(message):
        print(Utils.time_title(message))

    @staticmethod
    def send_message(notification_configs, message, **kwargs):
        if len(message) == 0:
            return

        # Wrapper for exception caught
        def invoke(func, configs):
            try:
                func(configs, message, **kwargs)
            except Exception as err:
                Utils.log(err)

        # DingTalk message
        invoke(Utils.send_dingtalk_message, notification_configs["dingtalk"])

        # Bark message
        invoke(Utils.send_bark_message, notification_configs["bark"])

        # Telegram message
        invoke(Utils.send_telegram_message, notification_configs["telegram"])

    @staticmethod
    def send_dingtalk_message(dingtalk_configs, message, **kwargs):
        if len(dingtalk_configs["access_token"]) == 0 or len(dingtalk_configs["secret_key"]) == 0:
            return

        timestamp = str(round(time.time() * 1000))
        secret_enc = dingtalk_configs["secret_key"].encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, dingtalk_configs["secret_key"])
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        headers = {
            'Content-Type': 'application/json'
        }

        params = {
            "access_token": dingtalk_configs["access_token"],
            "timestamp": timestamp,
            "sign": sign
        }

        content = {
            "msgtype": "text" if "message_type" not in kwargs else kwargs["message_type"],
            "text": {
                "content": message
            }
        }

        response = requests.post("https://oapi.dingtalk.com/robot/send", headers=headers, params=params, json=content)
        Utils.log("Dingtalk发送消息状态码：{}".format(response.status_code))

    @staticmethod
    def send_telegram_message(telegram_configs, message, **kwargs):
        if len(telegram_configs["bot_token"]) == 0 or len(telegram_configs["chat_id"]) == 0:
            return

        headers = {
            'Content-Type': 'application/json'
        }

        proxies = {
            "https": telegram_configs["http_proxy"],
        }

        content = {
            "chat_id": telegram_configs["chat_id"],
            "text": message
        }

        url = "https://api.telegram.org/bot{}/sendMessage".format(telegram_configs["bot_token"])
        response = requests.post(url, headers=headers, proxies=proxies, json=content)
        Utils.log("Telegram发送消息状态码：{}".format(response.status_code))

    @staticmethod
    def send_bark_message(bark_configs, message, **kwargs):
        if len(bark_configs["url"]) == 0:
            return

        url = "{}/{}".format(bark_configs["url"].strip("/"), urllib.parse.quote(message, safe=""))
        response = requests.post(url, params=bark_configs["query_parameters"])
        Utils.log("Bark发送消息状态码：{}".format(response.status_code))


class AppleStoreMonitor:
    def __init__(self, region='cn'):
        self.count = 1
        self.timeout = 10
        self.region = region
        
        # 加载地区配置
        with open('regions.json', encoding='utf-8') as f:
            self.regions_config = json.load(f)
        
        if region not in self.regions_config:
            raise ValueError(f"不支持的地区: {region}")
        
        self.region_info = self.regions_config[region]
        
        # 根据地区设置请求头
        self.headers = {
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'Referer': self.region_info['referer'],
            'DNT': '1',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
        }

    @staticmethod
    def config():
        """
        进行各类配置操作
        """
        # 加载地区配置
        with open('regions.json', encoding='utf-8') as f:
            regions_config = json.load(f)
        
        products_data = json.load(open('products.json', encoding='utf-8'))
        
        # 选择地区
        print('选择监控地区：')
        print('--------------------')
        region_keys = list(regions_config.keys())
        for index, region_key in enumerate(region_keys):
            print('[{}] {}'.format(index, regions_config[region_key]['name']))
        selected_region_index = int(input('选择要监控的地区：'))
        selected_region = region_keys[selected_region_index]
        
        products = products_data['regions'][selected_region]

        configs = {
            "region": selected_region,
            "selected_products": {},
            "selected_area": "",
            "exclude_stores": [],
            "notification_configs": {
                "dingtalk": {
                    "access_token": "",
                    "secret_key": ""
                },
                "telegram": {
                    "bot_token": "",
                    "chat_id": "",
                    "http_proxy": ""
                },
                "bark": {
                    "url": "",
                    "query_parameters": {
                        "url": None,
                        "isArchive": None,
                        "group": None,
                        "icon": None,
                        "automaticallyCopy": None,
                        "copy": None
                    }
                }
            },
            "scan_interval": 30,
            "alert_exception": False
        }

        while True:
            # chose product type
            print('--------------------')
            for index, item in enumerate(products):
                print('[{}] {}'.format(index, item))
            product_type = list(products)[int(input('选择要监控的产品：'))]

            # 检查产品数据结构
            product_data = products[product_type]
            
            # 判断是否有分类层级（中国大陆）还是直接是产品型号（香港）
            first_item_value = list(product_data.values())[0]
            has_classification = isinstance(first_item_value, dict)
            
            if has_classification:
                # 中国大陆的三层结构：产品类型 -> 产品分类 -> 产品型号
                # chose product classification
                print('--------------------')
                for index, (key, value) in enumerate(products[product_type].items()):
                    print('[{}] {}'.format(index, key))
                product_classification = list(products[product_type])[int(input('选择要监控的产品子类：'))]

                # chose product model
                print('--------------------')
                for index, (key, value) in enumerate(products[product_type][product_classification].items()):
                    print('[{}] {}'.format(index, value))
                product_model = list(products[product_type][product_classification])[int(input('选择要监控的产品型号：'))]

                configs["selected_products"][product_model] = (
                    product_classification, products[product_type][product_classification][product_model])
            else:
                # 香港的两层结构：产品类型 -> 产品型号
                print('--------------------')
                for index, (key, value) in enumerate(products[product_type].items()):
                    print('[{}] {}'.format(index, value))
                product_model = list(products[product_type])[int(input('选择要监控的产品型号：'))]

                configs["selected_products"][product_model] = (
                    product_type, products[product_type][product_model])

            print('--------------------')
            if len(input('是否添加更多产品[Enter继续添加，非Enter键退出]：')) != 0:
                break

        # config area
        region_info = regions_config[selected_region]
        monitor = AppleStoreMonitor(selected_region)
        
        print('选择计划预约的地址：')
        url_param = region_info['location_params']
        choice_params = {}
        param_dict = {}
        
        if len(url_param) > 0:  # 中国大陆需要选择省市区
            for step, param in enumerate(url_param):
                print('请稍后...{}/{}'.format(step + 1, len(url_param)))
                response = requests.get(region_info['base_url'] + region_info['address_lookup_endpoint'], 
                                        headers=monitor.headers, params=choice_params)
                result_param = json.loads(response.text)['body'][param]
                if type(result_param) is dict:
                    result_data = result_param['data']
                    print('--------------------')
                    for index, item in enumerate(result_data):
                        print('[{}] {}'.format(index, item['value']))
                    input_index = int(input('请选择地区序号：'))
                    choice_result = result_data[input_index]['value']
                    param_dict[param] = choice_result
                    choice_params[param] = param_dict[param]
                else:
                    choice_params[param] = result_param

            print('正在加载网络资源...')
            response = requests.get(region_info['base_url'] + region_info['address_lookup_endpoint'], 
                                    headers=monitor.headers, params=choice_params)
            selected_area = json.loads(response.text)['body'][region_info['location_key']]
        else:  # 香港等地区使用固定位置
            if selected_region == 'hk':
                selected_area = region_info.get('default_location', 'Hong Kong')
            else:
                selected_area = region_info['name']
        
        configs["selected_area"] = selected_area

        print('--------------------')
        print("选择的计划预约的地址是：{}，加载预约地址周围的直营店...".format(selected_area))

        store_params = {
            "location": selected_area,
            "parts.0": list(configs["selected_products"].keys())[0]
        }
        
        # 为香港地区添加额外参数
        if selected_region == 'hk':
            store_params["mt"] = "regular"
            import time
            store_params["_"] = int(time.time() * 1000)
        response = requests.get(region_info['base_url'] + region_info['fulfillment_endpoint'],
                                headers=monitor.headers, params=store_params)

        # 添加响应状态检查和调试信息
        if response.status_code != 200:
            print(f"API请求失败，状态码：{response.status_code}")
            print(f"响应内容：{response.text}")
            return
        
        # 检查响应内容是否为空
        if not response.text.strip():
            print("API返回空响应，请检查网络连接或稍后重试")
            return
        
        try:
            response_data = json.loads(response.text)
            print(f"调试信息 - API响应结构：{list(response_data.keys())}")
            
            # 检查响应结构 - 支持不同地区的API格式
            if 'body' not in response_data:
                print("API响应格式异常：缺少'body'字段")
                print(f"完整响应：{response.text}")
                return
            
            # 香港地区使用不同的API结构
            if selected_region == 'hk':
                if 'stores' not in response_data['body']:
                    print("API响应格式异常：缺少'stores'字段（香港API）")
                    print(f"完整响应：{response.text}")
                    return
                stores = response_data['body']['stores']
            else:
                # 中国大陆等地区的API结构
                if 'content' not in response_data['body']:
                    print("API响应格式异常：缺少'content'字段")
                    print(f"完整响应：{response.text}")
                    return
                
                if 'pickupMessage' not in response_data['body']['content']:
                    print("API响应格式异常：缺少'pickupMessage'字段")
                    print(f"完整响应：{response.text}")
                    return
                
                if 'stores' not in response_data['body']['content']['pickupMessage']:
                    print("API响应格式异常：缺少'stores'字段")
                    print(f"完整响应：{response.text}")
                    return
                
                stores = response_data['body']['content']['pickupMessage']['stores']
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误：{e}")
            print(f"响应内容：{response.text}")
            return
        except Exception as e:
            print(f"处理API响应时发生错误：{e}")
            print(f"响应内容：{response.text}")
            return
        for index, store in enumerate(stores):
            # 根据不同地区的API结构获取地址信息
            if selected_region == 'hk':
                # 香港API的地址结构
                address_parts = []
                if "address" in store and "address2" in store["address"]:
                    address_parts.append(store["address"]["address2"])
                if "address" in store and "address3" in store["address"]:
                    address_parts.append(store["address"]["address3"])
                address = "，".join(filter(None, address_parts)) or "地址信息不可用"
            else:
                # 中国大陆API的地址结构
                address = store["retailStore"]["address"]["street"]
            
            print("[{}] {}，地址：{}".format(index, store["storeName"], address))

        exclude_stores_indexes = input('排除无需监测的直营店，输入序号[直接回车代表全部监测，多个店的序号以空格分隔]：').strip().split()
        if len(exclude_stores_indexes) != 0:
            print("已选择的无需监测的直营店：{}".format("，".join(list(map(lambda i: stores[int(i)]["storeName"], exclude_stores_indexes)))))
            configs["exclude_stores"] = list(map(lambda i: stores[int(i)]["storeNumber"], exclude_stores_indexes))

        print('--------------------')
        # config notification configurations
        notification_configs = configs["notification_configs"]

        # config dingtalk notification
        dingtalk_access_token = input('输入钉钉机器人Access Token[如不配置直接回车即可]：')
        dingtalk_secret_key = input('输入钉钉机器人Secret Key[如不配置直接回车即可]：')

        # write dingtalk configs
        notification_configs["dingtalk"]["access_token"] = dingtalk_access_token
        notification_configs["dingtalk"]["secret_key"] = dingtalk_secret_key

        # config telegram notification
        print('--------------------')
        telegram_chat_id = input('输入Telegram机器人Chat ID[如不配置直接回车即可]：')
        telegram_bot_token = input('输入Telegram机器人Token[如不配置直接回车即可]：')
        telegram_http_proxy = input('输入Telegram HTTP代理地址[如不配置直接回车即可]：')

        # write telegram configs
        notification_configs["telegram"]["chat_id"] = telegram_chat_id
        notification_configs["telegram"]["bot_token"] = telegram_bot_token
        notification_configs["telegram"]["http_proxy"] = telegram_http_proxy

        # config bark notification
        print('--------------------')
        bark_url = input('输入Bark URL[如不配置直接回车即可]：')

        # write dingtalk configs
        notification_configs["bark"]["url"] = bark_url

        # 输入扫描间隔时间
        print('--------------------')
        configs["scan_interval"] = int(input('输入扫描间隔时间[以秒为单位，默认为30秒，如不配置直接回车即可]：') or 30)

        # 是否对异常进行告警
        print('--------------------')
        configs["alert_exception"] = (input('是否在程序异常时发送通知[Y/n，默认为n]：').lower().strip() or "n") == "y"

        with open('apple_store_monitor_configs.json', 'w') as file:
            json.dump(configs, file, indent=2)
            print('--------------------')
            print("扫描配置已生成，并已写入到{}文件中\n请使用 python {} start 命令启动监控".format(file.name, os.path.abspath(__file__)))

    def start(self):
        """
        开始监控
        """
        configs = json.load(open('apple_store_monitor_configs.json', encoding='utf-8'))
        
        # 如果配置中有地区信息，更新当前实例的地区
        if 'region' in configs:
            self.region = configs['region']
            self.region_info = self.regions_config[self.region]
            self.headers['Referer'] = self.region_info['referer']
        
        selected_products = configs["selected_products"]
        selected_area = configs["selected_area"]
        exclude_stores = configs["exclude_stores"]
        notification_configs = configs["notification_configs"]
        scan_interval = configs["scan_interval"]
        alert_exception = configs["alert_exception"]
        alert_startup = configs.get("alert_startup", True)  # 默认为True保持向后兼容

        products_info = []
        for index, product_info in enumerate(selected_products.items()):
            products_info.append("【{}】{}".format(index, " ".join(product_info[1])))
        message = "准备开始监测，地区：{}\n商品信息如下：\n{}\n取货区域：{}\n扫描频次：{}秒/次".format(
            self.region_info['name'], "\n".join(products_info), selected_area, scan_interval)
        Utils.log(message)
        if alert_startup:
            Utils.send_message(notification_configs, message)

        params = {
            "location": selected_area,
            "mt": "regular",
        }

        code_index = 0
        product_codes = selected_products.keys()
        for product_code in product_codes:
            params["parts.{}".format(code_index)] = product_code
            code_index += 1

        # 上次整点通知时间
        last_exactly_time = -1
        while True:
            available_list = []
            tm_hour = time.localtime(time.time()).tm_hour
            try:
                # 更新请求时间
                params["_"] = int(time.time() * 1000)

                response = requests.get(self.region_info['base_url'] + self.region_info['fulfillment_endpoint'],
                                        headers=self.headers,
                                        params=params,
                                        timeout=self.timeout)

                json_result = json.loads(response.text)
                
                # 根据不同地区的API结构获取stores数据
                if self.region == 'hk':
                    # 香港地区API结构
                    stores = json_result['body']['stores']
                else:
                    # 中国大陆等地区API结构
                    stores = json_result['body']['content']['pickupMessage']['stores']
                Utils.log(
                    '-------------------- 第{}次扫描 --------------------'.format(
                        self.count + 1))
                for item in stores:
                    store_name = item['storeName']
                    if item["storeNumber"] in exclude_stores:
                        print("【{}：已排除】".format(store_name))
                        continue
                    print("{:-<100}".format("【{}】".format(store_name)))
                    for product_code in product_codes:
                        pickup_search_quote = item['partsAvailability'][product_code]['pickupSearchQuote']
                        pickup_display = item['partsAvailability'][product_code]['pickupDisplay']
                        store_pickup_product_title = item['partsAvailability'][product_code]['messageTypes']['regular']['storePickupProductTitle']
                        print('\t【{}】{}'.format(pickup_search_quote, store_pickup_product_title))
                        # 根据地区判断可用状态
                        available_statuses = [self.region_info['available_status']]
                        if 'available_status_alt' in self.region_info:
                            available_statuses.append(self.region_info['available_status_alt'])
                        
                        is_available = (pickup_search_quote in available_statuses or 
                                        pickup_display != 'unavailable')
                        if is_available:
                            available_list.append((store_name, product_code, store_pickup_product_title))

                if len(available_list) > 0:
                    messages = []
                    print("命中货源，请注意 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    Utils.log("以下直营店预约可用：")
                    for item in available_list:
                        messages.append("【{}】 {}".format(item[0], item[2]))
                        print("【{}】{}".format(item[0], item[2]))
                    print("命中货源，请注意 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                    Utils.send_message(notification_configs,
                                       Utils.time_title(
                                           "第{}次扫描到直营店有货，信息如下：\n{}".format(self.count, "\n".join(messages))))

            except Exception as err:
                Utils.log(err)
                # 6:00 ~ 23:00才发送异常消息
                if alert_exception and 6 <= tm_hour <= 23:
                    Utils.send_message(notification_configs,
                                       Utils.time_title("第{}次扫描出现异常：{}".format(self.count, repr(err))))

            if len(available_list) == 0:
                interval = max(random.randint(int(scan_interval / 2), scan_interval * 2), 5)
                Utils.log('{}秒后进行第{}次尝试...'.format(interval, self.count))

                # 整点通知已禁用 - 只在有货或异常时才通知
                # if last_exactly_time != tm_hour and (6 <= tm_hour <= 23):
                #     Utils.send_message(notification_configs,
                #                        Utils.time_title("已扫描{}次，扫描程序运行正常".format(self.count)))
                #     last_exactly_time = tm_hour
                time.sleep(interval)
            else:
                time.sleep(5)

            # 次数自增
            self.count += 1


if __name__ == '__main__':
    args = sys.argv

    if len(args) < 2 or len(args) > 3:
        print("""
        Usage: python {} <option> [region]
        option can be:
        \tconfig: pre config of products or notification
        \tstart: start to monitor
        region can be:
        \tcn: 中国大陆 (default)
        \thk: 香港
        """.format(args[0]))
        exit(1)

    # 获取地区参数，默认为中国大陆
    region = args[2] if len(args) == 3 else 'cn'

    if args[1] == "config":
        AppleStoreMonitor.config()

    if args[1] == "start":
        AppleStoreMonitor(region).start()
