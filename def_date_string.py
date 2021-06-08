# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 06:32:42 2020

@author: alex1
"""

from datetime import date, timedelta

def date_string(date_format="%Y%m%d"):

    dt_1 = date.today() + timedelta(0) #-1 y day 0 today +1 tomorrow
    dtx = str((dt_1.strftime(date_format)))
    return(dtx)

#my_date = date_string()
