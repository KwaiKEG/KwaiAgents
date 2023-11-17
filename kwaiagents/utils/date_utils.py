from datetime import datetime
from lunar_python import Solar, Lunar
import pandas as pd


def fix_date_to_format(date, format="%Y-%M-%d"):
    d = pd.to_datetime(date, format=format)
    return d.strftime(format)


def get_date_list(start_date, end_date):
    date_list = []
    start_date_list = start_date.split("-")
    s_y = int(start_date_list[0])
    s_m = int(start_date_list[1])
    s_d = int(start_date_list[2])

    end_date_list = end_date.split("-")
    e_y = int(end_date_list[0])
    e_m = int(end_date_list[1])
    e_d = int(end_date_list[2])

    c_y = s_y
    c_m = s_m
    c_d = s_d

    days = 0

    flag = 0
    while days <= 100:
        if c_y == e_y and c_m == e_m and c_d == e_d:
            flag = 1
        
        date_list.append(str(c_y) + '-' + str("%02d" % c_m) + '-' + str("%02d" % c_d))

        # 获取指定年份每月有几天
        d = Solar.fromYmd(c_y, 1, 1)
        if d.isLeapYear():
            day_dict = {
                1: 31,
                2: 29,
                3: 31,
                4: 30,
                5: 31,
                6: 30,
                7: 31,
                8: 31,
                9: 30,
                10: 31,
                11: 30,
                12: 31,
            }
        else:
            day_dict = {
                1: 31,
                2: 28,
                3: 31,
                4: 30,
                5: 31,
                6: 30,
                7: 31,
                8: 31,
                9: 30,
                10: 31,
                11: 30,
                12: 31,
            }

        if c_d == day_dict[c_m]:  # 本月最后一天
            if c_m == 12:  # 12月
                c_y += 1
                c_m = 1
                c_d = 1
            else:
                c_m += 1
                c_d = 1
        else:
            c_d += 1

        days += 1

        if flag == 1:
            break
    return date_list


def get_current_time_and_date(lang="en"):
    solar = Solar.fromDate(datetime.now())
    lunar = solar.getLunar()
    if lang == "zh":
        rst = f'''
当前阳历日期和时间: {str(datetime.now())}
当前星期: 星期{str(solar.getWeekInChinese())}
当前农历日期: {str(lunar.toString())}
当前时辰: {str(lunar.getTimeZhi())}时
'''.strip()
    else:
        rst = f'''
Current Gregorian date and time: {str(datetime.now())}
Current day of the week: 星期{str(solar.getWeekInChinese())}
Current lunar date: {str(lunar.toString())}
Current Chinese time unit: {str(lunar.getTimeZhi())}时
'''.strip()
    return rst