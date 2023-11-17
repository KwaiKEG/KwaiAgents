#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: PAN Leyi
# Email:  panleyi@kuaishou.com


from kwaiagents.tools.base import BaseResult, BaseTool
from datetime import datetime
from ephem import *
import math

solar_terms = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]


class SolarTermsResult(BaseResult):
    @property
    def answer(self):
        if not self.json_data:
            return ""
        else:
            item = self.json_data
            print(item)
            rst = ""
            for main_key in item.keys():
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


class SolarTermsTool(BaseTool):
    """
    Retrieve solar terms in Chinese for a given year. 

    Args:
        year (int): Target year for query.

    Returns:
        str: Solar terms information of the given year.
    """
    name = "get_solar_terms_info"
    zh_name = "查询节气日期"
    description = 'Get solar terms info:"get_solar_terms_info", args:"year": <int, required>'
    tips = "get_solar_terms_info retrieve solar terms in Chinese for a given year."

    def __init__(
        self,
        max_search_nums=5,
        lang="wt-wt",
        max_retry_times=5,
        *args,
        **kwargs,
    ):
        self.max_search_nums = max_search_nums
        self.max_retry_times = max_retry_times
        self.lang = lang

    def __call__(self, year, *args, **kwargs):
        # 计算黄经
        def ecliptic_lon(jd_utc):
            s = Sun(jd_utc)  # 构造太阳
            equ = Equatorial(
                s.ra, s.dec, epoch=jd_utc
            )  # 求太阳的视赤经视赤纬（epoch设为所求时间就是视赤经视赤纬）
            e = Ecliptic(equ)  # 赤经赤纬转到黄经黄纬
            return e.lon  # 返回黄纬

        # 根据时间求太阳黄经，计算到了第几个节气，春分序号为0
        def sta(jd):
            e = ecliptic_lon(jd)
            n = int(e * 180.0 / math.pi / 15)
            return n

        # 根据当前时间，求下个节气的发生时间
        def iteration(jd, sta):  # jd：要求的开始时间，sta：不同的状态函数
            s1 = sta(jd)  # 初始状态(太阳处于什么位置)
            s0 = s1
            dt = 1.0  # 初始时间改变量设为1天
            while True:
                jd += dt
                s = sta(jd)
                if s0 != s:
                    s0 = s
                    dt = -dt / 2  # 使时间改变量折半减小
                if abs(dt) < 0.0000001 and s != s1:
                    break
            return jd
        
        res = []
        jd = Date(datetime(int(year), 1, 1, 0, 0, 0))
        e = ecliptic_lon(jd)
        for i in range(24):
            jd = iteration(jd, sta)
            d = Date(jd + 1 / 3).tuple()
            res.append({"节气": solar_terms[i], "日期": "{0}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(d[0], d[1], d[2], d[3], d[4], int(d[5]))})

        return SolarTermsResult({
                f"{year}年节气表": res
            })
