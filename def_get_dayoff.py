from make_holidaycsv import get_holidays
from datetime import datetime, timedelta
import pandas as pd


def get_dayoff(dayback=0):

    # df_holidays = get_holidays()
    df_holidays = pd.read_csv('d:/anaconda/holidays.csv')
    df_holidays['tradingDate'] = pd.to_datetime(df_holidays['tradingDate'], format='%d-%b-%Y').dt.strftime('%d-%m-%Y')
    holiday_list = df_holidays['tradingDate'].tolist()

    dt_1 = datetime.today() - timedelta(dayback)  # -1 for yday and 0 for today
    if dt_1.strftime('%d-%m-%Y') in holiday_list:
        is_holiday = 1
    else:
        is_holiday = 0
    weekday = dt_1.strftime('%A')
    if is_holiday == 0 and weekday != 'Saturday' and weekday != 'Sunday':
        holiday = 0
    else:
        holiday = 1

    return holiday
