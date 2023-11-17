#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: PAN Leyi
# Email:  panleyi@kuaishou.com


import datetime
import math
import requests

from ephem import *
from lunar_python import Lunar, Solar
import pandas as pd
from kwaiagents.tools.base import BaseResult, BaseTool
from kwaiagents.utils.date_utils import get_date_list


class CalendarResult(BaseResult):
    @property
    def answer(self):
        if not self.json_data:
            return ""
        else:
            item = self.json_data
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


class CalendarTool(BaseTool):
    """
    Retrieve calendar details between specified dates.
    Provide information on date, week day, solar term, zodiac, and holidays, but DO NOT provide the current time.

    Args:
        start_date (str): Start date in the format "yyyy-MM-dd".
        end_date (str): End date in the format "yyyy-MM-dd".

    Returns:
        str: Calendar details spanning from start date to end date.
    """
    name = "get_calendar_info"
    zh_name = "日历查询"
    description = 'Get calendar info:"get_calendar_info", args:"start_date":<str, "yyyy-MM-dd">, "end_date":<str, "yyyy-MM-dd">'
    tips = "get_calendar_info provide information on date, week day, solar term, zodiac, and holidays, but DO NOT provide the current time."

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

    def __call__(self, start_date, end_date, *args, **kwargs):

        date_list = get_date_list(start_date, end_date)

        huangli_str = []

        for date in date_list:
            l = date.split("-")
            c_y = int(l[0])
            c_m = int(l[1])
            c_d = int(l[2])
            d = Solar.fromYmd(c_y, c_m, c_d)
            lunar = d.getLunar()
            yinli = (
                lunar.getYearInChinese()
                + "年"
                + lunar.getMonthInChinese()
                + "月"
                + lunar.getDayInChinese()
                + " "
                + lunar.getYearInGanZhi()
                + "年"
            )
            yangli = (
                str(d.getYear())
                + "年"
                + str(d.getMonth())
                + "月"
                + str(d.getDay())
                + "日"
                + " 星期"
                + d.getWeekInChinese()
            )
            shengxiao = lunar.getYearShengXiao()
            xingzuo = d.getXingZuo()
            jieqi = lunar.getJieQi()
            jieri = ""
            l = lunar.getFestivals()
            for s in l:
                jieri += s + " "
            l = lunar.getOtherFestivals()
            for s in l:
                jieri += s + " "
            l = d.getFestivals()
            for s in l:
                jieri += s + " "
            l = d.getOtherFestivals()
            for s in l:
                jieri += s + " "

            huangli_str.append({"阳历": yangli, "阴历": yinli, "生肖": shengxiao, "星座": xingzuo, "节气": jieqi, "节日": jieri})

        return CalendarResult(
            {
                "待查日历信息": huangli_str,
            }
        )
