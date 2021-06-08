from datetime import date,timedelta
import holidays
import pandas as pd

"uncomment on every new year to fetch holiday csv from nse url"
def hol(root='path'):

    df_holidays = pd.read_csv(root + 'indian_holidays.csv')

    df_holidays = df_holidays.set_index('date', drop=False)
    h_dict = df_holidays[['holiday']].to_dict()

    custom_holidays = holidays.HolidayBase()

    custom_holidays.append(h_dict['holiday'])
    return custom_holidays

def check(dayback=0,root='path'):
    dt_1 = date.today() + timedelta(dayback)
    sday = dt_1.strftime('%Y-%m-%d')
    #mhol = check(sday)
    custom_holidays = hol(root)
    fact = sday in custom_holidays
    return fact


def market_off(dayback=0,root='path'):

    mdate=date.today()+timedelta(dayback)
    msday=mdate.strftime('%A')
    sday = mdate.strftime('%Y-%m-%d')
    mhol = check(dayback,root)

    if msday!='Saturday' and msday!='Sunday' and mhol==False:
        market_off=False
    else:
        market_off=True

    return(market_off, sday)

#my_week = market_off(dayback=-1,root='C:/Users/alex1/PycharmProjects/bhav/')
