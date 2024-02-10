import requests
from zipfile import ZipFile
from io import BytesIO,StringIO
from def_get_dayoff import get_dayoff
import pandas as pd
import datetime
from datetime import datetime, timedelta
import math
import mibian
from def_expiry import expiry
import numpy as np
# from def_custom_tabulate import custom_tabulate

# from kaleido.scopes.plotly import PlotlyScope  # pip install kaleido

# dayback=0  # dayback = 1 = yday, 0 today
def get_options(dayback =0):
    """

    :param dayback:
    :return: df_final, df_pain
    :type: list
    """
    # C "The India 10-Year Government Bond Yield" is used ; Google text in quotes and it will show.
    # risk_free_rate = 7.04

    timeindex_list = []
    ceiv_mean_list = []
    peiv_mean_list = []
    pcroi_list = []
    pcrwt_list = []
    activeputoi_list = []
    activeput_list = []
    activecalloi_list = []
    activecall_list = []
    long_sum_list = []
    short_sum_list = []
    longliq_sum_list = []
    shortcover_sum_list = []
    ceunwind_sum_list = []
    peunwind_sum_list = []
    activeputoimx_list = []
    activeputmx_list = []
    activecalloimx_list = []
    activecallmx_list = []
    nifty_v_list = []
    nifty_l_list = []
    nifty_o_list = []
    nifty_h_list = []
    nifty_price_list = []
    maxPain_list = []

    # dayback = 8
    dt_1 = datetime.today() - timedelta(dayback)  # -1 for yday and 0 for today
    # print('date: ', dt_1)

    is_holiday = get_dayoff(dayback=dayback)
    if is_holiday == 0:
        # C proceed only if it's not holiday or weekend so we save some computational power
        try:
            root = 'd:/demos/'

            # datenow = datetime.datetime.now()
            year = dt_1.strftime('%Y')
            month_num = dt_1.strftime('%m')
            date_num = dt_1.strftime('%d')
            month = dt_1.strftime('%b')

            expiry_list = expiry(int(year))
            # C To get the expiry date of the asked month of the year
            exp_day = expiry_list[int(month_num)]
            exp_int1 = datetime.strptime(exp_day, '%d-%m-%Y').date()
            exp_int = int(exp_int1.strftime('%Y%m%d'))
            now_int = int(dt_1.strftime('%Y%m%d'))
            if now_int < exp_int:
                exp_day_format = datetime.strptime(exp_day, '%d-%m-%Y').date()
                exp_month = exp_day_format.strftime('%b')
                expirydate = exp_day_format.strftime('%d-' + exp_month + '-%Y')
                print('expiry date ', expirydate)
            else:
                exp_day = expiry_list[int(month_num) + 1]
                exp_day_format = datetime.strptime(exp_day, '%d-%m-%Y').date()
                exp_month = exp_day_format.strftime('%b')
                expirydate = exp_day_format.strftime('%d-' + exp_month + '-%Y')
                print('expiry date rolled for next month', expirydate)

            print('date: ', dt_1)
            month_today = dt_1.strftime("%b")
            m_m = month_today.upper()
            sday = dt_1.strftime('%d' + m_m + '%Y')
            year = dt_1.strftime("%Y")

            print('expiry date ', expirydate)

            url = f'https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{year}/{m_m}/fo{sday}bhav.csv.zip'
            got_headers = {'Connection': 'keep-alive',
                       'authority': 'www.nseindia.com',
                       'path': '/api/marketStatus',
                       'Origin': 'https://www1.nseindia.com',
                       'Referer': 'https://www1.nseindia.com/products/content/equities/equities/archieve_eq.htm',
                       'Sec-Fetch-Mode': 'cors',
                       'Sec-Fetch-Site': 'same-origin',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

            request = requests.get(url, headers=got_headers)
            print(request.status_code)

            if request.status_code == 200:

                with ZipFile(BytesIO(request.content)) as zip_file:
                    # Extract all files in the zip to a temporary directory
                    zip_file.extractall(f'{root}storage/')

                ds = f'fo{sday}bhav.csv'
                qs = f'{root}storage/{ds}'
                df1 = pd.read_csv(qs, header='infer', skiprows=0)
                df2 = df1[df1['SYMBOL'] == 'NIFTY']
                df3 = df2[df2['EXPIRY_DT'] == expirydate]

                df3 = df3.reset_index()
                nifty_price = df3.iloc[0]['CLOSE']
                nifty_o = df3.iloc[0]['OPEN']
                nifty_h = df3.iloc[0]['HIGH']
                nifty_l = df3.iloc[0]['LOW']
                nifty_v = df3.iloc[0]['CONTRACTS'] * 75

                df4 = df3.drop(axis=0, index=0)
                # print(custom_tabulate(df4))
                # df4['TIMESTAMP'] = df4['TIMESTAMP'].dt
                # df4['diff'] = df4['TIMESTAMP']-df4['EXPIRY_DT']
                # def roundup(x):
                #     return int(math.ceil(x / 100.0)) * 100  # replace ceil with floor for lower round 100
                #
                # roundc = roundup(nifty_price)  # upper round number in 100 use it for call

                def rounddn(x):
                    return int(math.floor(x / 100.0)) * 100

                # print(custom_tabulate(df))
                roundp = rounddn(nifty_price)  # Lower round number for put
                # dfsmall1 = df3[df3['STRIKE_PR'] <= roundp + 600]
                dfsmall1 = df4[df4.loc[:, 'STRIKE_PR'] <= roundp + 600]
                dfsmall2 = dfsmall1[dfsmall1.loc[:, 'STRIKE_PR'] >= roundp - 500]
                dfsmall_ce = dfsmall2[dfsmall2.loc[:, 'OPTION_TYP'] == 'CE']
                dfsmall_pe = dfsmall2[dfsmall2.loc[:, 'OPTION_TYP'] == 'PE']
                dfsmall_ce = dfsmall_ce.iloc[::2]
                dfsmall_pe = dfsmall_pe.iloc[::2]
                # todo: IV
                dfsmall_ce = dfsmall_ce.reset_index()
                dfsmall_pe = dfsmall_pe.reset_index()

                # mibian.BS([Underlying Price, Strike Price, Interest Rate, Days To Expiration], Call/Put Price)
                days_to_exp = (exp_day_format - dt_1.date()).days
                # Function to calculate implied volatility using mibian.BS for apply method to increase spead
                def calculate_iv(row):
                    try:
                        result = mibian.BS([nifty_price, row['STRIKE_PR'], 0, days_to_exp],
                                     callPrice=row['CLOSE']).impliedVolatility
                        return result
                    except:
                        return None

                dfsmall_ce['iv'] = 0.0  # Initialize the 'iv' column with zeros
                # Apply the function to calculate implied volatility for each row
                dfsmall_ce['iv'] = dfsmall_ce.apply(calculate_iv, axis=1)

                def calculate_iv_pe(row):
                    try:
                        result = mibian.BS([nifty_price, row['STRIKE_PR'], 0, days_to_exp],
                                     putPrice=row['CLOSE']).impliedVolatility
                        return result
                    except:
                        return None

                dfsmall_pe['iv'] = 0.0  # Initialize the 'iv' column with zeros
                # Apply the function to calculate implied volatility for each row
                dfsmall_pe['iv'] = dfsmall_pe.apply(calculate_iv_pe, axis=1)
                peloss_1st = []
                for p in range(0, len(dfsmall_pe)):
                    peloss_i = dfsmall_pe.iloc[p]['OPEN_INT'] * (100 * p)
                    peloss_1st.append(peloss_i)
                denom_a = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                demon_b = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                loss_len = len(peloss_1st)

                peloss_mainlist = []
                pe_seriesloss_l = [sum(peloss_1st)]  # this is the main value we're looking for

                for lo in range(0, loss_len - 1):
                    # lo = 0
                    denom_main = [i / j for i, j in zip(denom_a[lo:], demon_b[:-(lo + 1)])]
                    peloss_list = [i / j for i, j in zip(peloss_1st[lo + 2:], denom_main)]
                    peloss_mainlist.append(peloss_list)
                    pe_seriesloss_l.append(sum(peloss_list))
                dfsmall_ce_inv = dfsmall_ce.copy().sort_values('STRIKE_PR', axis=0, ascending=False, inplace=False,
                                                               kind='quicksort', na_position='last')

                celoss_1st = []
                for c in range(0, len(dfsmall_ce)):
                    celoss_i = dfsmall_ce_inv.iloc[c]['OPEN_INT'] * (100 * c)
                    celoss_1st.append(celoss_i)
                denom_ca = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                demon_cb = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                loss_clen = len(celoss_1st)

                celoss_mainlist = []
                ce_seriesloss_l = [sum(celoss_1st)]  # this is the main value we looking for

                for clo in range(0, loss_clen - 1):
                    # clo = 0
                    denom_cmain = [i / j for i, j in zip(denom_ca[clo:], demon_cb[:-(clo + 1)])]
                    celoss_list = [i / j for i, j in zip(celoss_1st[clo + 2:], denom_cmain)]
                    celoss_mainlist.append(celoss_list)
                    ce_seriesloss_l.append(sum(celoss_list))

                ce_seriesloss_l.reverse()  # reverse sort order
                netloss_list = [i + j for i, j in zip(pe_seriesloss_l, ce_seriesloss_l)]
                df_pain = pd.DataFrame({'Strikes': dfsmall_pe['STRIKE_PR'].to_list(), 'Pain': netloss_list})

                df_pain['Mp_strike'] = np.where(df_pain['Pain'] == df_pain['Pain'].min(), df_pain['Strikes'], 0)
                max_pain = df_pain['Mp_strike'].max()
                df_pain['CE_IV'] = dfsmall_ce['iv']
                df_pain['PE_IV'] = dfsmall_pe['iv']

                df_pain['ceOPEN_INT'] = dfsmall_ce['OPEN_INT']
                df_pain['peOPEN_INT'] = dfsmall_pe['OPEN_INT']
                df_pain['ceCHG_IN_OI'] = dfsmall_ce['CHG_IN_OI']
                df_pain['peCHG_IN_OI'] = dfsmall_pe['CHG_IN_OI']

                # todo: pcr open interest pcr weighted
                pcroi = round(dfsmall_pe['OPEN_INT'].sum() / dfsmall_ce['OPEN_INT'].sum(), 2)
                pcrwt = round(dfsmall_pe['VAL_INLAKH'].sum() / dfsmall_ce['VAL_INLAKH'].sum(), 2)

                # todo: active ce and active ce oi
                rep = dfsmall_ce['CHG_IN_OI'].abs()
                rep = rep.astype('float64')
                valu = rep.idxmax()
                activecall = dfsmall_ce.iloc[valu]['STRIKE_PR']
                activecalloi = dfsmall_ce.iloc[valu]['OPEN_INT']
                ceiv_mean = round(dfsmall_ce['iv'].mean(), 2)

                # todo: active put and active pe oi
                rep_pe = dfsmall_pe['CHG_IN_OI'].abs()
                rep_pe = rep_pe.astype('float64')
                valu_pe = rep_pe.idxmax()
                activeput = dfsmall_pe.iloc[valu_pe]['STRIKE_PR']
                activeputoi = dfsmall_pe.iloc[valu_pe]['OPEN_INT']
                peiv_mean = round(dfsmall_pe['iv'].mean(), 2)
                # todo: max oi ce strike and max ce oi
                repmx = dfsmall_ce['OPEN_INT'].abs()
                repmx = repmx.astype('float64')
                valumx = repmx.idxmax()
                activecallmx = dfsmall_ce.iloc[valumx]['STRIKE_PR']
                activecalloimx = dfsmall_ce.iloc[valumx]['OPEN_INT']

                # todo: max oi pe strike and max pe oi
                rep_mxpe = dfsmall_pe['OPEN_INT'].abs()
                rep_mxpe = rep_mxpe.astype('float64')
                valu_mxpe = rep_mxpe.idxmax()
                activeputmx = dfsmall_pe.iloc[valu_mxpe]['STRIKE_PR']
                activeputoimx = dfsmall_pe.iloc[valu_mxpe]['OPEN_INT']


                # todo ce unwinding
                list_ce_unwind = (dfsmall_ce[dfsmall_ce['CHG_IN_OI'] < 0]).STRIKE_PR.to_list()
                list_pe_unwind = (dfsmall_pe[dfsmall_pe['CHG_IN_OI'] < 0]).STRIKE_PR.to_list()


                # todo list top 20 only futures oi addition with scenarios
                df_no_nf = df1[df1['OPTION_TYP'] == 'XX']  # C XX = not Options, only Futures
                # df_no_bnf = df_no_nf[df_no_nf['SYMBOL'] != 'BANKNIFTY']
                df_no_nf_current = df_no_nf.copy()[df_no_nf['EXPIRY_DT'] == expirydate]
                df_no_bnf_current = df_no_nf_current.sort_values('VAL_INLAKH', ascending=False)
                df_active10 = df_no_bnf_current.head(100)

                long_buildup_toplist = df_active10[(df_active10['CHG_IN_OI'] >= 0) &
                                                   (df_active10['CLOSE'] >= df_active10['OPEN'])].SYMBOL.to_list()
                short_cover_toplist = df_active10[(df_active10['CHG_IN_OI'] < 0) &
                                                  (df_active10['CLOSE'] >= df_active10['OPEN'])].SYMBOL.to_list()

                long_liquid_toplist = df_active10[(df_active10['CHG_IN_OI'] < 0) &
                                                  (df_active10['CLOSE'] < df_active10['OPEN'])].SYMBOL.to_list()

                short_buildup_toplist = df_active10[(df_active10['CHG_IN_OI'] >= 0) &
                                                    (df_active10['CLOSE'] < df_active10['OPEN'])].SYMBOL.to_list()

                long_sum =len(long_buildup_toplist)
                short_sum = len(short_buildup_toplist)
                longliq_sum = len(long_liquid_toplist)
                shortcover_sum = len(short_cover_toplist)
                ceunwind_sum = len(list_ce_unwind)
                peunwind_sum = len(list_pe_unwind)

                # dtx = dt_1.strftime("%Y%m%d")

                activeputoimx_list.append(activeputoimx)
                activeputmx_list.append(activeputmx)
                activecalloimx_list.append(activecalloimx)
                activecallmx_list.append(activecallmx)
                nifty_o_list.append(nifty_o)
                nifty_h_list.append(nifty_h)
                nifty_l_list.append(nifty_l)
                nifty_price_list.append(nifty_price)
                nifty_v_list.append(nifty_v)

                ceiv_mean_list.append(ceiv_mean)
                peiv_mean_list.append(peiv_mean)
                pcroi_list.append(pcroi)
                pcrwt_list.append(pcrwt)
                activeputoi_list.append(activeputoi)
                activeput_list.append(activeput)
                activecalloi_list.append(activecalloi)
                activecall_list.append(activecall)
                long_sum_list.append(long_sum)
                short_sum_list.append(short_sum)
                longliq_sum_list.append(longliq_sum)
                shortcover_sum_list.append(shortcover_sum)
                ceunwind_sum_list.append(ceunwind_sum)
                peunwind_sum_list.append(peunwind_sum)
                maxPain_list.append(max_pain)
                timeindex = dt_1.strftime('%Y%m%dT')
                timeindex_list.append(timeindex)

                """
                For Options 5 strikes from ATM above and below that is 10 strikes used. Skipped odd strikes 
                eg. 18050, 19050
                For Long_Sum and below column Values are calculated Like this if open interest is higher and closes higher
                 than open then it considered long interest and if the  
                Open interest is higher but close is lower than the open then it is considered short open interest  
                Similar type of logic is applied for other variables.
                Note that we calculated sum of those filtered scrips   
                For this calculation the data frame is sorted by highest traded volume in values 
                and then only top 20 contracts considered 
                Four put and call unwinding number we filtered CEs and PEs that shows negative change in open interest
                """
                df_final = pd.DataFrame({
                    'TimeIndex': timeindex_list,
                    'MX_PEOI': activeputoimx_list,  # C Max OI PE/CE
                    'MX_PE': activeputmx_list,
                    'MX_CEOI': activecalloimx_list,
                    'MX_CE': activecallmx_list,
                    'Nifty_O': nifty_o_list,
                    'Nifty_H':nifty_h_list,
                    'Nifty_L': nifty_l_list,
                    'Nifty_Close': nifty_price_list,
                    'Nifty_V': nifty_v_list,
                    'CEIV_Mean': ceiv_mean_list,
                    'PEIV_Mean': peiv_mean_list,
                    'PCR_OI': pcroi_list,
                    'PCR_WT': pcrwt_list,
                    'ActivePEOI': activeputoi_list,  # C Active = Max change in OI PE/CE abs value used
                    'ActivePE': activeput_list,
                    'ActiveCEOI': activecalloi_list,
                    'ActiveCE': activecall_list,
                    'Long_Sum': long_sum_list,
                    'Short_Sum': short_sum_list,
                    'LongLiq_Sum': longliq_sum_list,
                    'ShortCover_Sum': shortcover_sum_list,
                    'CE_Unwind_Sum': ceunwind_sum_list,
                    'PE_Unwind_Sum': peunwind_sum_list,
                    'MaxPain': maxPain_list
                })
            else:
                df_final = {}
                df_pain = {}
        except Exception as s:
            print(s)
            print(f'No data')
            df_final = {}
            df_pain = {}

    else:
        print(' Its Trading Holiday')
        df_final = {}
        df_pain = {}

    return df_final, df_pain
