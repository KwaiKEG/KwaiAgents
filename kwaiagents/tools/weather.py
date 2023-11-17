#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: PAN Leyi
# Email:  panleyi@kuaishou.com


from itertools import islice
import json
import os
import random
import requests
import traceback
from translate import Translator
from datetime import datetime

from kwaiagents.config import Config
from kwaiagents.tools.base import BaseResult, BaseTool
from kwaiagents.utils.date_utils import get_date_list, fix_date_to_format


KEY = os.getenv("WEATHER_API_KEY")
URL_CURRENT_WEATHER = "http://api.weatherapi.com/v1/current.json"
URL_FORECAST_WEATHER = "http://api.weatherapi.com/v1/forecast.json"
URL_HISTORY_WEATHER = "http://api.weatherapi.com/v1/history.json"


def translate_text(text):
    translator = Translator(to_lang="Chinese")
    translation = translator.translate(text)
    return translation


class WeatherResult(BaseResult):
    @property
    def answer(self):
        if not self.json_data:
            return ""
        else:
            item = self.json_data
            print(item)
            if "error" in json.dumps(item):
                if item["start_date"] == item["end_date"]:
                    return f'天气工具无法查询到{item["location"]}在{item["start_date"]}这一天天气，建议用网页搜索'
                else:
                    return f'天气工具无法查询到{item["location"]}在{item["start_date"]}和{item["end_date"]}之间的天气，建议用网页搜索'
            rst = ""
            for main_key in item.keys():
                if isinstance(item[main_key], str):
                    continue
                if len(item[main_key]) != 0:
                    rst += f"{main_key}： \n"
                    keys = item[main_key][0].keys()
                    rst += ' | ' + ' | '.join(keys) + ' | ' + '\n'
                    for i in range(len(keys)):
                        rst += ' | ' + '---'
                    rst += ' |\n'

                    for row in item[main_key]:
                        rst += ' | ' + ' | '.join(row.values()) + ' | ' + '\n'
                rst += "\n"
            return rst


class WeatherTool(BaseTool):
    """
    Retrieve weather information for specified locations and dates.

    Args:
        location (str): Locations in English separated by commas, e.g., "Beijing,Vancouver,...,Chicago".
        start_date (str): Start date in format "yyyy-MM-dd".
        end_date (str): End date in format "yyyy-MM-dd".
        is_current (str): "yes" or "no" indicating if current time's weather is desired.

    Returns:
        str: Weather information between start date and end date.
    """
    name = "get_weather_info"
    zh_name = "查询天气"
    description = 'Get weather info:"get_weather_info", args:"location": <location1,location2,...,in English,required>, "start_date":"<str: yyyy-MM-dd, required>", "end_date":"<str: yyyy-MM-dd, required>", "is_current":"<str, yes or no, required>"'
    tips = ""

    location_c2e ={
        # 中国主要省市
        "上海": "Shanghai",
        "云南": "Yunnan",
        "内蒙古": "Inner Mongolia",
        "北京": "Beijing",
        "台湾": "Taiwan",
        "吉林": "Jilin",
        "四川": "Sichuan",
        "天津": "Tianjin",
        "宁夏": "Ningxia",
        "安徽": "Anhui",
        "山东": "Shandong",
        "山西": "Shanxi",
        "广东": "Guangdong",
        "广西": "Guangxi",
        "新疆": "Xinjiang",
        "江苏": "Jiangsu",
        "江西": "Jiangxi",
        "河北": "Hebei",
        "河南": "Henan",
        "浙江": "Zhejiang",
        "海南": "Hainan",
        "湖北": "Hubei",
        "湖南": "Hunan",
        "澳门": "Macao",
        "甘肃": "Gansu",
        "福建": "Fujian",
        "西藏": "Tibet",
        "贵州": "Guizhou",
        "辽宁": "Liaoning",
        "重庆": "Chongqing",
        "陕西": "Shaanxi",
        "青海": "Qinhai",
        "香港": "Hong Kong",
        "黑龙江": "Heilongjiang",
        "石家庄": "Shijiazhuang",
        "太原": "Taiyuan",
        "呼和浩特": "Huhehaote",
        "沈阳": "Shenyang",
        "长春": "Changchun",
        "哈尔滨": "Haerbin",
        "南京": "Nanjing",
        "杭州": "Hangzhou",
        "合肥": "Hefei",
        "福州": "Fuzhou",
        "济南": "Jinan",
        "南昌": "Nanchang",
        "郑州": "Zhengzhou",
        "乌鲁木齐": "Urumqi",
        "武汉": "Wuhan",
        "长沙": "Changsha",
        "广州": "Guangzhou",
        "南宁": "Nanning",
        "海口": "Haikou",
        "成都": "Chengdu",
        "贵阳": "Guiyang",
        "昆明": "Kunming",
        "拉萨": "Lasa",
        "西安": "Xi'an",
        "西宁": "Xining",
        "兰州": "Lanzhou",
        "银川": "Yinchuan",
        "深圳": "Shenzhen",
        "苏州": "Suzhou",
        "东莞": "Dongwan",
        "宁波": "Ningbo",
        "佛山": "Foshan",
        "青岛": "Qingdao",
        "无锡": "Wuxi",
        "厦门": "Xiamen",
        "温州": "Wenzhou",
        "金华": "Jinhua",
        "大连": "Dalian",
        "泉州": "Quanzhou",
        "惠州": "Huizhou",
        "常州": "Changzhou",
        "嘉兴": "Jiaxing",
        "徐州": "Xuzhou",
        "南通": "Nantong",
        "保定": "Baoding",
        "珠海": "Zhuhai",
        "中山": "Zhongshan",
        "临沂": "Linyi",
        "潍坊": "Weifang",
        "烟台": "Yantai",
        "绍兴": "Shaoxing",
        "台州": "Taizhou",
        "洛阳": "Luoyang",
        "廊坊": "Langfang",
        "汕头": "Shantou",
        "湖州": "Huzhou",
        "咸阳": "Xianyang",
        "盐城": "Yancheng",
        "济宁": "Jining",
        "扬州": "Yangzhou",
        "赣州": "Ganzhou",
        "阜阳": "Fuyang",
        "唐山": "Tangshan",
        "镇江": "Zhenjiang",
        "邯郸": "Handan",
        "南阳": "Nanyang",
        "桂林": "Guilin",
        "泰州": "Taizhou",
        "遵义": "Zunyi",
        "江门": "Jiangmen",
        "揭阳": "Jieyang",
        "芜湖": "Wuhu",
        "商丘": "Shangqiu",
        "连云港": "Lianyunguang",
        "新乡": "Xinxiang",
        "淮安": "Huaian",
        "淄博": "Zibo",
        "绵阳": "Mianyang",
        "菏泽": "Heze",
        "漳州": "Zhangzhou",
        "周口": "Zhoukou",
        "沧州": "Cangzhou",
        "信阳": "Xinyang",
        "衡阳": "Hengyang",
        "湛江": "Zhanjiang",
        "三亚": "Sanya",
        "上饶": "Shangrao",
        "邢台": "Xingtai",
        "莆田": "Putian",
        "柳州": "Liuzhou",
        "宿迁": "Suqian",
        "九江": "Jiujiang",
        "襄阳": "Xiangyang",
        "驻马店": "Zhumadian",
        "宜昌": "Yichang",
        "岳阳": "Yueyang",
        "肇庆": "Zhaoqing",
        "滁州": "Chuzhou",
        "威海": "Weihai",
        "德州": "Dezhou",
        "泰安": "Taian",
        "安阳": "Anyang",
        "荆州": "Jingzhou",
        "运城": "Yuncheng",
        "安庆": "Anqing",
        "潮州": "Chaozhou",
        "清远": "Qingyuan",
        "开封": "Kaifeng",
        "宿州": "Suzhou",
        "株洲": "Zhuzhou",
        "蚌埠": "Bengbu",
        "许昌": "Xuchang",
        "宁德": "Ningde",
        "六安": "Liuan",
        "宜春": "Yichun",
        "聊城": "Liaocheng",
        "渭南": "Weinan",
        "宜宾": "Yibin",
        "鞍山": "Anshan",
        "南充": "Nanchong",
        "秦皇岛": "Qinhuangdao",
        "毫州": "Haozhou",
        "常德": "Changde",
        "晋中": "Jinzhong",
        "孝感": "Xiaogan",
        "丽水": "Lishui",
        "平顶山": "Pingdingshan",
        "黄冈": "Huanggang",
        "龙岩": "Longyan",
        "枣庄": "Zaozhuang",
        "郴州": "Chenzhou",
        "日照": "Rizhao",
        "马鞍山": "Maanshan",
        "衢州": "Quzhou",
        "鄂尔多斯": "Ordos Barun Gar Domda",
        "包头": "Baotou",
        "邵阳": "Shaoyang",
        "德阳": "Deyang",
        "泸州": "Luzhou",
        "临汾": "Linfen",
        "南平": "Nanping",
        "焦作": "Jiaozuo",
        "宣城": "Xuancheng",
        "毕节": "Bijie",
        "淮南": "Huainan",
        "黔南": "Qiannan",
        "滨州": "Binzhou",
        "黔东南": "Qiandongnan",
        "茂名": "Maoming",
        "三明": "Sanming",
        "湘潭": "Xiangtan",
        "梅州": "Meizhou",
        "乐山": "Leshan",
        "黄石": "Huangshi",
        "韶关": "Shaoguan",
        "衡水": "Hengshui",
        "怀化": "Huaihua",
        "张家口": "Zhangjiakou",
        "永州": "Yongzhou",
        "十堰": "Shiyan",
        "曲靖": "Qujing",
        "大庆": "Daqing",
        "舟山": "Zhoushan",
        "宝鸡": "Baoji",
        "景德镇": "Jingdezhen",
        "北海": "Beihai",
        "娄底": "Loudi",
        "汕尾": "Shanwei",
        "锦州": "Jinzhou",
        "咸宁": "Xianning",
        "大同": "Datong",
        "恩施": "Enshi",
        "营口": "Yingkou",
        "长治": "Changzhi",
        "赤峰": "Chifeng",
        "抚州": "Fuzhou",
        "漯河": "Luohe",
        "眉山": "Meishan",
        "东营": "Dongying",
        "铜仁": "Tongren",
        "汉中": "Hanzhong",
        "黄山": "Huangshan",
        "阳江": "Yangjiang",
        "大理": "Dali",
        "盘锦": "Panjin",
        "达州": "Dazhou",
        "承德": "Chengde",
        "红河": "Honghe",
        "百色": "Baise",
        "丹东": "Dandong",
        "益阳": "Yiyang",
        "濮阳": "Puyang",
        "河源": "Heyuan",
        "铜陵": "Tongling",
        "鄂州": "Ezhou",
        "内江": "Neijiang",
        "梧州": "Wuzhou",
        "淮北": "Huaibei",
        "安顺": "Anshun",
        "晋城": "Jincheng",

        # 外国主要城市
        "夏威夷檀香山": "Honolulu",
        "阿拉斯加安克雷奇": "Anchorage",
        "温哥华": "Vancouver",
        "旧金山": "San Francisco",
        "西雅图": "Seattle",
        "洛杉矶": "Los Angeles",
        "阿克拉维克": "Aklavik",
        "艾德蒙顿": "Edmonton",
        "凰城": "Phoenix",
        "丹佛": "Denver",
        "墨西哥城": "Mexico City",
        "温尼伯": "Winnipeg",
        "休斯敦": "Houston",
        "明尼亚波利斯": "Minneapolis",
        "圣保罗": "St. Paul",
        "新奥尔良": "New Orleans",
        "芝加哥": "Chicago",
        "蒙哥马利": "Montgomery",
        "危地马拉": "Guatemala",
        "圣萨尔瓦多": "San Salvador",
        "特古西加尔巴": "Tegucigalpa",
        "马那瓜": "Managua",
        "哈瓦那": "Havana",
        "印地安纳波利斯": "Indianapolis",
        "亚特兰大": "Atlanta",
        "底特律": "Detroit",
        "华盛顿": "Washington DC",
        "费城": "Philadelphia",
        "多伦多": "Toronto",
        "渥太华": "Ottawa",
        "拿骚": "Nassau",
        "利马": "Lima",
        "金斯敦": "Kingston",
        "波哥大": "Bogota",
        "纽约": "New York",
        "蒙特利尔": "Montreal",
        "波士顿": "Boston",
        "圣多明各": "Santo Domingo",
        "拉帕兹": "La Paz",
        "加拉加斯": "Caracas",
        "圣胡安": "San Juan",
        "哈里法克斯": "Halifax",
        "圣地亚哥": "Santiago",
        "亚松森": "Asuncion",
        "布宜诺斯艾利斯": "Buenos Aires",
        "蒙特维的亚": "Montevideo",
        "巴西利亚": "Brasilia",
        "圣保罗": "Sao Paulo",
        "里约热内卢": "Rio de Janeiro",
        "雷克雅未克": "Reykjavik",
        "里斯本": "Lisbon",
        "卡萨布兰卡": "Casablanca",
        "都柏林": "Dublin",
        "伦敦": "London",
        "马德里": "Madrid",
        "巴塞罗那": "Barcelona",
        "巴黎": "Paris",
        "拉各斯": "Lagos",
        "阿尔及尔": "Algiers",
        "布鲁塞尔": "Brussels",
        "阿姆斯特丹": "Amsterdam",
        "日内瓦": "Geneva",
        "苏黎世": "Zurich",
        "法兰克福": "Frankfurt",
        "奥斯陆": "Oslo",
        "哥本哈根": "Copenhagen",
        "罗马": "Rome",
        "柏林": "Berlin",
        "布拉格": "Prague",
        "萨格雷布": "Zagreb",
        "维也纳": "Vienna",
        "斯德哥尔摩": "Stockholm",
        "布达佩斯": "Budapest",
        "贝尔格莱德": "Belgrade",
        "华沙": "Warsaw",
        "开普敦": "Cape Town",
        "索非亚": "Sofia",
        "雅典城": "Athens",
        "塔林": "Tallinn",
        "赫尔辛基": "Helsinki",
        "布加勒斯特": "Bucharest",
        "明斯克": "Minsk",
        "约翰尼斯堡": "Johannesburg",
        "伊斯坦布尔": "Istanbul",
        "基辅": "Kyiv",
        "敖德萨": "Odesa",
        "哈拉雷": "Harare",
        "开罗": "Cairo",
        "安卡拉": "Ankara",
        "耶路撒冷": "Jerusalem",
        "贝鲁特": "Beirut",
        "安曼": "Amman",
        "喀土穆": "Khartoum",
        "内罗毕": "Nairobi",
        "莫斯科": "Moscow",
        "亚的斯亚贝巴": "Addis Ababa",
        "巴格达": "Baghdad",
        "亚丁": "Aden",
        "利雅得": "Riyadh",
        "安塔那那利佛": "Antananarivo",
        "科威特城": "Kuwait City",
        "德黑兰": "Tehran",
        "阿布扎比": "Abu Dhabi",
        "喀布尔": "Kabul",
        "卡拉奇": "Karachi",
        "塔什干": "Tashkent",
        "伊斯兰堡": "Islamabad",
        "拉合尔": "Lahore",
        "孟买": "Mumbai",
        "新德里": "New Delhi",
        "柯尔喀塔": "Kolkata",
        "加德满都": "Kathmandu",
        "达卡": "Dhaka",
        "仰光": "Yangon",
        "金边": "Phnom Penh",
        "曼谷": "Bangkok",
        "河内": "Hanoi",
        "雅加达": "Jakarta",
        "吉隆坡": "Kuala Lumpur",
        "新加坡": "Singapore",
        "珀斯": "Perth",
        "马尼拉": "Manila",
        "首尔": "Seoul",
        "东京": "Tokyo",
        "达尔文": "Darwin",
        "布里斯班": "Brisbane",
        "墨尔本": "Melbourne",
        "堪培拉": "Canberra",
        "悉尼": "Sydney",
        "亚特雷德": "Adelaide",
        "堪察加" :"Kamchatka",
        "阿纳德尔": "Anadyr",
        "苏瓦": "Suva",
        "惠灵顿": "Wellington",
        "查塔姆群岛": "Chatham Island",
        "圣诞岛": "Kiritimati",
    }

    location_e2c = {}


    def __init__(
        self,
        cfg=None,
        max_search_nums=5,
        lang="wt-wt",
        max_retry_times=5,
        *args,
        **kwargs,
    ):
        self.cfg = cfg if cfg else Config()
        self.max_search_nums = max_search_nums
        self.max_retry_times = max_retry_times
        self.lang = lang
        for key in self.location_c2e:
            value = self.location_c2e[key]
            self.location_e2c[value] = key
            self.location_e2c[value.lower()] = key 


    def get_current_weather(self, location: str):
        """Get current weather"""
        if location == "default" or location == "Default" or location == "Default Country" or location == "default country":
            location = "Beijing"
        param = {"key": KEY, "q": location, "aqi": "yes"}
        res_completion = requests.get(URL_CURRENT_WEATHER, params=param)
        data = json.loads(res_completion.text.strip())
        if "error" in data.keys():
            return {"查询结果": "error"}
        
        # print(data["current"])

        output = {}
        overall = translate_text(f"{data['current']['condition']['text']}")[0]
        output["整体天气"] = f"{overall}"
        if "temp_c" in data['current'] and data['current']['temp_c']:
            output[
                "气温"
            ] = f"{data['current']['temp_c']}(°C)"
        if "precip_mm" in data['current'] and data['current']['precip_mm']:
            output[
                "降雨量"
            ] = f"{data['current']['precip_mm']}(mm)"
        if "pressure_mb" in data['current'] and data['current']['pressure_mb']:
            output["气压"] = f"{data['current']['pressure_mb']}(百帕)"
        if "humidity" in data['current'] and data['current']['humidity']:
            output["湿度"] = f"{data['current']['humidity']}"
        if "feelslike_c" in data['current'] and data['current']['feelslike_c']:
            output[
                "体感温度"
            ] = f"{data['current']['feelslike_c']}(°C)"
        if "vis_km" in data['current'] and data['current']['vis_km']:
            output[
                "能见度"
            ] = f"{data['current']['vis_km']}(km)"
        if "air_quality" in data["current"] and data['current']['air_quality']:
            output[
                "空气质量"
            ] = f"pm2.5: {round(data['current']['air_quality']['pm2_5'], 2)}(μg/m3), pm10: {round(data['current']['air_quality']['pm10'], 2)}(μg/m3)"

        return output

    def forecast_weather(self, location: str, date: str):
        """Forecast weather in the upcoming days."""
        if location == "default" or location == "Default" or location == "Default Country" or location == "default country":
            param = {"key": KEY, "q": "Beijing", "dt": date, "aqi": "yes"}
        else:
            param = {"key": KEY, "q": location, "dt": date, "aqi": "yes"}
        res_completion = requests.get(URL_FORECAST_WEATHER, params=param)
        res_completion = json.loads(res_completion.text.strip())
        if "error" in res_completion.keys():
            return {"查询结果": "error"}
        
        res_completion_item = res_completion["forecast"]["forecastday"][0]
        output_dict = {}
        for k, v in res_completion_item["day"].items():
            output_dict[k] = v
        for k, v in res_completion_item["astro"].items():
            output_dict[k] = v
        output = {}
        output["日期"] = str(date)
        overall = translate_text(f"{output_dict['condition']['text']}")[0]
        output["整体天气"] = f"{overall}"
        output[
            "最高温度"
        ] = f"{output_dict['maxtemp_c']}(°C)"
        output[
            "最低温度"
        ] = f"{output_dict['mintemp_c']}(°C)"
        output[
            "平均温度"
        ] = f"{output_dict['avgtemp_c']}(°C)"
        output["降雨概率"] = f"{output_dict['daily_chance_of_rain']}"
        output["降雪概率"] = f"{output_dict['daily_will_it_snow']}"
        output[
            "平均能见度"
        ] = f"{output_dict['avgvis_km']}(km)"
        output["平均湿度"] = f"{output_dict['avghumidity']}"
        output["日出时间"] = f"{output_dict['sunrise']}"
        output["日落时间"] = f"{output_dict['sunset']}"
        if "air_quality" not in output_dict.keys() or len(output_dict["air_quality"].keys()) == 0:
            output["空气质量"] = ""
        else:
            output[
                "空气质量"
            ] = f"pm2.5: {round(output_dict['air_quality']['pm2_5'], 2)}(μg/m3), pm10: {round(output_dict['air_quality']['pm10'], 2)}(μg/m3)"

        return output

    def get_history_weather(self, location: str, date: str):
        """Find weather of a past date."""
        if location == "default" or location == "Default" or location == "Default Country" or location == "default country":
            param = {"key": KEY, "q": "Beijing", "dt": date}
        else:
            param = {"key": KEY, "q": location, "dt": date}
        
        res_completion = requests.get(URL_HISTORY_WEATHER, params=param)
        res_completion = json.loads(res_completion.text.strip())
        if "error" in res_completion.keys():
            return {"查询结果": "error"}

        res_completion = res_completion["forecast"]["forecastday"][0]
        output_dict = {}
        for k, v in res_completion["day"].items():
            output_dict[k] = v
        for k, v in res_completion["astro"].items():
            output_dict[k] = v

        output = {}
        output["日期"] = str(date)
        overall = translate_text(f"{output_dict['condition']['text']}")[0]
        output["整体天气"] = f"{overall}"
        output[
            "最高温度"
        ] = f"{output_dict['maxtemp_c']}(°C)"
        output[
            "最低温度"
        ] = f"{output_dict['mintemp_c']}(°C)"
        output[
            "平均温度"
        ] = f"{output_dict['avgtemp_c']}(°C)"
        output[
            "降雨量"
        ] = f"{output_dict['totalprecip_mm']}(mm)"
        output[
            "平均能见度"
        ] = f"{output_dict['avgvis_km']}(km)"
        output["平均湿度"] = f"{output_dict['avghumidity']}"
        output["日出时间"] = f"{output_dict['sunrise']}"
        output["日落时间"] = f"{output_dict['sunset']}"

        return output

    def get_weather(self, location, start_date, end_date, is_current):
        start_date = fix_date_to_format(start_date)
        end_date = fix_date_to_format(end_date)
        if location == "default" or location == "Default" or location == "Default Country" or location == "default country":
            location_c = "北京"
        # elif location in self.location_e2c.keys():
        #     location_c = self.location_e2c[location]
        else:
            location_c = self.location_e2c[location]

        final_dict = {}
        
        date_list = get_date_list(start_date, end_date)

        # 获取现在的时间
        curr_date = str(datetime.now())[:10]
        # 全都是history
        if end_date <= curr_date:
            res = []
            for d in date_list:
                if d == curr_date:
                    try:
                        res.append(self.get_history_weather(location, d))
                    except:
                        res.append(self.forecast_weather(location, d))
                else:
                    res.append(self.get_history_weather(location, d))
                
            if start_date == end_date:
                final_dict[f"{location_c}{start_date}天气"] = res
            else:
                final_dict[f"{location_c}{start_date}至{end_date}天气"] = res

        # 全都是forecast
        elif start_date > curr_date:
            res = []
            i = 0
            for d in date_list:
                if i >= 10:
                    break
                res.append(self.forecast_weather(location, d))
                i += 1
            if start_date == end_date:
                final_dict[f"{location_c}{start_date}天气预报"] = res
            else:
                final_dict[f"{location_c}{start_date}至{end_date}天气预报"] = res

        else:
            res = []
            # 有的是history，有的是forecast
            past_date_list = get_date_list(start_date, curr_date)
            future_date_list = (get_date_list(curr_date, end_date))[1:]
            for d in past_date_list:
                if d == curr_date:
                    try:
                        res.append(self.get_history_weather(location, d))
                    except:
                        res.append(self.forecast_weather(location, d))
                else:
                    res.append(self.get_history_weather(location, d))

            if start_date == curr_date:
                final_dict[f"{location_c}{start_date}天气"] = res
            else:
                final_dict[f"{location_c}{start_date}至{curr_date}天气"] = res
            res = []
            i = 0
            for d in future_date_list:
                if i >= 10:
                    break
                res.append(self.forecast_weather(location, d))
                i += 1
            if future_date_list[0] == end_date:
                final_dict[f"{location_c}{end_date}天气预报"] = res
            else:
                final_dict[f"{location_c}{future_date_list[0]}至{end_date}天气预报"] = res


        if is_current == "yes":

            final_dict[f"此时此刻{location_c}天气"] = [self.get_current_weather(location)]

        return final_dict


    def __call__(self, start_date, end_date, is_current="yes", location="Beijing", *args, **kwargs):
        
        final_res = {
            "location": location,
            "start_date": start_date,
            "end_date": end_date
        }

        # 如果还是给了多个地址
        if ',' in location:
            location_list = location.split(',')
        elif '，' in location:
            location_list = location.split('，')
        else:
            location_list = [location]
        
        for location_ in location_list:
            location_ = location_.strip()
            # 如果给的是中文，且在字典中，则查字典翻译
            if location_ in self.location_c2e.keys():
                loc = self.location_c2e[location_]
            # 如果给的是中文，且不在字典中，直接返回结果不存在
            elif not (32 <= ord(location_[0]) <= 126):
                final_res['查询结果'] = 'error'
                return WeatherResult(final_res)
            # 如果是英文，且在字典中，直接输进去
            elif location_ in self.location_e2c.keys():
                loc = location_
            # 如果是英文，且不在字典中，返回不存在
            else:
                final_res['查询结果'] = 'error'
                return WeatherResult(final_res)
            # print(loc)
            
            if is_current == "是":
                is_cur = "yes"
            elif is_current == "否" or is_current == "不是":
                is_cur = "no"
            else:
                is_cur = is_current
            try:
                result = self.get_weather(
                        loc, start_date, end_date, is_cur
                    )
                final_res.update(result)
            except:
                print(traceback.format_exc())
                final_res['查询结果'] = 'error'

        return WeatherResult(final_res)