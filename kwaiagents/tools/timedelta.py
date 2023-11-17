#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: PAN Leyi
# Email:  panleyi@kuaishou.com

from datetime import datetime
from dateutil.relativedelta import relativedelta

from kwaiagents.config import Config
from kwaiagents.tools.base import BaseResult, BaseTool


class TimeDeltaResult(BaseResult):
    @property
    def answer(self):
        item = self.json_data
        rst = ""
        for key in item.keys():
            rst += f'{key}: {item[key]}\n'
        return rst


class TimeDeltaTool(BaseTool):
    """
    Calculate the time interval between two timestamps.

    Args:
        start_time (str): format of "yyyy-MM-dd HH:mm:ss".
        end_time (str): format of "yyyy-MM-dd HH:mm:ss".

    Returns:
        str: The time delta between start time and end time.
    """
    name = "time_delta"
    zh_name = "时间差工具"
    description = 'time delta:"time_delta", args:"start_time":<str, "yyyy-MM-dd HH:mm:ss">, "end_time":<str, "yyyy-MM-dd HH:mm:ss">'
    tips = "time_delta calculate the time interval between two timestamps."

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

    def __call__(self, start_time, end_time, *args, **kwargs):
        # 长度为10，只有年月日
        if len(start_time) == 10:
            start_time += " 00:00:00"
        if len(end_time) == 10:
            end_time += " 00:00:00"
        d1 = datetime.strptime(start_time[:19], '%Y-%m-%d %H:%M:%S')
        d2 = datetime.strptime(end_time[:19], '%Y-%m-%d %H:%M:%S')
        if d1 > d2:
            t = d1
            d1 = d2
            d2 = t
        delta = d2 - d1
        delta_years = delta.days // 365
        delta_months = (delta.days % 365) // 30
        delta_days = (delta.days % 365) % 30

        return TimeDeltaResult(
            {
                f"{d1}和{d2}距离相差": f"{delta}; {delta_years}年{delta_months}个月{delta_days}天"
            }
        )