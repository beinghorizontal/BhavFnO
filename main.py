import requests
import zipfile
import io
import pandas as pd
import datetime
from def_market_off import market_off
from def_date_string import date_string
import math
import mibian
from def_expiry import expiry
import numpy as np
# from kaleido.scopes.plotly import PlotlyScope  # pip install kaleido (another method to save plotly html graph as png)
from scipy.stats import norm # needed for norm error in windows

path = 'C:/Users/alex1/PycharmProjects/bhav/'


def bhav_options(dayback=-1,root=path):  # dayback = -2 = yday, 0 today
    try:

        market_is_off = market_off(dayback,root)[0]
        """
        Url to save bhvcopy and other options related data such as IV, OI etc  
        """

        """
        Get expiry date
        
        Generating expiry date was the most trickiest part. The logic is 1st get current month,
        then last Thursday of month, then check if holiday is there else shift one day before,
        then check if current date is greater than expiry if so shift to next month 
        """
        datenow = datetime.date.today() + datetime.timedelta(dayback)
        year = datenow.strftime('%Y')
        month_num = datenow.strftime('%m')

        expiry_list = expiry(year =int(year),root=root)
        exp_day = expiry_list[int(month_num)]
        exp_int1 = datetime.datetime.strptime(exp_day, '%d-%m-%Y').date()
        exp_int = int(exp_int1.strftime('%Y%m%d'))
        now_int = int(datenow.strftime('%Y%m%d'))

        "if current date < expiry"
        if now_int < exp_int:
            exp_day_format = datetime.datetime.strptime(exp_day, '%d-%m-%Y').date()
            exp_month = exp_day_format.strftime('%b')
            expirydate = exp_day_format.strftime('%d-' + exp_month + '-%Y')
            print('expiry date ', expirydate)
        else:
            exp_day = expiry_list[int(month_num) + 1]
            exp_day_format = datetime.datetime.strptime(exp_day, '%d-%m-%Y').date()
            exp_month = exp_day_format.strftime('%b')
            expirydate = exp_day_format.strftime('%d-' + exp_month + '-%Y')
            print('expiry date rolled for next month', expirydate)

        exp_int_new = datetime.datetime.strptime(exp_day, '%d-%m-%Y').date()
        exp_int_new = int(exp_int_new.strftime('%Y%m%d'))

        dt_1 = datetime.date.today() + datetime.timedelta(dayback)  # -1 for yday and 0 for today

        """
        It 1st checks if selected date for bhavcopy is holiday or weekend which is useful for
        running the same code in loop to download several historical bhavcopies

        Bhavcopy url is dynamic i.e. it changes as month and date changes so we keep the constant
        part in url as it is and create variable for dynamic part using datetime library and scrape
        bhavcopy using requests. As usual I am not relying on some NSE scraping library which makes
        code fragile.

        Example of an url:
        If current F&O series is 2021 Jun and selected date for bhavcopy(default is previous day)
        is 1st June 2021 then bhavcopy url looks like this (do note that it's a zip file)
        #'http://www1.nseindia.com/content/historical/DERIVATIVES/2021/JUN/fo01JUN2021bhav.csv.zip'
        """

        if not market_is_off:
            month_today = dt_1.strftime("%b")
            m_m = month_today.upper()# NSE URL specific format
            sday = dt_1.strftime('%d' + m_m + '%Y')
            year = dt_1.strftime("%Y")

            url = "http://www1.nseindia.com/content/historical/DERIVATIVES/" + year + "/" + m_m + "/fo" + sday + "bhav.csv.zip"

            got_headers = {'Connection': 'keep-alive',
                           'Host': 'www1.nseindia.com',
                           'Origin': 'https://www1.nseindia.com',
                           'Referer': 'https://www1.nseindia.com/products/content/derivatives/equities/archieve_fo.htm',
                           'Sec-Fetch-Mode': 'cors',
                           'Sec-Fetch-Site': 'same-origin',
                           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}

            request = requests.get(url, headers=got_headers)
            zipDocument = zipfile.ZipFile(io.BytesIO(request.content))
            """
            To avoid clutter it will create folder name 'storage' if not already and store Bhavcopies
            using dynamic filename ex. fo<todayd_date>bhav.csv
            """
            zipDocument.extractall(root + 'storage/')
            ds = 'fo' + sday + 'bhav.csv'
            qs = root + 'storage/' + ds
            "read earlier unzipped csv"
            df1 = pd.read_csv(qs, header='infer', skiprows=0)
            "Bhavcopy contains all F&O scrips but we also need to create Nifty specific dataframe for index F&O"
            df2 = df1[df1['SYMBOL'] == 'NIFTY']
            "Keep rows for only current month F&O series"
            df3 = df2[df2['EXPIRY_DT'] == expirydate]
            df3 = df3.reset_index()
            """
            We need Nifty Futures last quote to get ATM strike
            Also, for IVs we are going to use Nifty F instead of spot as underlying while
            keeping interest rate 0 (#NIFTYFUTURES premium take cares of risk free interest rate)
            """
            nifty_price = df3.iloc[0]['CLOSE']
            nifty_o = df3.iloc[0]['OPEN']
            nifty_h = df3.iloc[0]['HIGH']
            nifty_l = df3.iloc[0]['LOW']
            nifty_v = df3.iloc[0]['CONTRACTS'] * 75
            """
            Get At The Money strike (ATM) by simply using floor value of Nifty F last closing price
            For ex. if last closing price for NF is 15608 then floor is 15600 which is our ATM
            """

            df4 = df3.drop(axis=0, index=0) #  dropped unwanted 1st row

            def rounddn(x):
                return int(math.floor(x / 100.0)) * 100

            roundp = rounddn(nifty_price)  # Lower round number for put

            """
            Here major change from existing practice. As we know far OTM strikes on NSE are not that liquid like
            the US so we have to adjust accordingly and remove noise. How?
            Get 10 strikes near ATM in multiples of x100 (avoid 16050,17050) as they tend to be most
            traded contracts.
            """
            dfsmall1 = df4[df4.loc[:, 'STRIKE_PR'] <= roundp + 600]
            dfsmall2 = dfsmall1[dfsmall1.loc[:, 'STRIKE_PR'] >= roundp - 500]
            dfsmall_ce = dfsmall2[dfsmall2.loc[:, 'OPTION_TYP'] == 'CE']
            dfsmall_pe = dfsmall2[dfsmall2.loc[:, 'OPTION_TYP'] == 'PE']
            dfsmall_ce = dfsmall_ce.iloc[::2]
            dfsmall_pe = dfsmall_pe.iloc[::2]

            "Now since our own mini option chain is ready, let's calculate IVs using Mibian library"
            dfsmall_ce = dfsmall_ce.reset_index()
            dfsmall_pe = dfsmall_pe.reset_index()

            "mibian.BS([Underlying Price, Strike Price, Interest Rate, Days To Expiration], Call/Put Price)"

            days_to_exp = (exp_day_format - datenow).days
            ceivlist = []
            # Mibian BS function is tough to vectorize, so we have to use for loop here
            for lence in range(len(dfsmall_ce)):
                #lence=0
                #mibian.BS([nifty_price ,  dfsmall_ce.iloc[lence]['STRIKE_PR'], 0, days_to_exp], 22).callPrice #get CE price
                iv = mibian.BS([nifty_price, dfsmall_ce.iloc[lence]['STRIKE_PR'], 0, days_to_exp],
                               callPrice=dfsmall_ce.iloc[lence]['CLOSE']).impliedVolatility
                ceivlist.append(iv)

            dfsmall_ce['iv'] = ceivlist

            peivlist = []
            for lenpe in range(len(dfsmall_pe)):
                #lenpe = 9
                peiv = mibian.BS([nifty_price, dfsmall_pe.iloc[lenpe]['STRIKE_PR'], 0, days_to_exp],
                                 putPrice=dfsmall_pe.iloc[lenpe]['CLOSE']).impliedVolatility
                peivlist.append(peiv)
            dfsmall_pe['iv'] = peivlist

#...........................................................................................................

            """
            Calculate max pain
            
            If you don't know max pain then to know more read this
            https://zerodha.com/varsity/chapter/max-pain-pcr-ratio/
            """
            # 1st Put strikes
            peloss_1st = []
            for p in range(0,len(dfsmall_pe)):
                #p = 2
                # print(dfsmall_pe.iloc[p]['STRIKE_PR'])
                peloss_i = dfsmall_pe.iloc[p]['OPEN_INT']*(100* p)
                peloss_1st.append(peloss_i)
            #shortcut method to calculate loss per strike
            # Idea is OI of a single strike remains the same while strikes changes by constant number i,e,100
            denom_a = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            demon_b = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            loss_len = len(peloss_1st)

            peloss_mainlist = []
            pe_seriesloss_l = [sum(peloss_1st)] # this is the main value we looking for

            for lo in range(0, loss_len-1):
                # lo = 0
                denom_main = [i / j for i, j in zip(denom_a[lo:], demon_b[:-(lo + 1)])]
                peloss_list = [i / j for i, j in zip(peloss_1st[lo + 2:], denom_main)]
                peloss_mainlist.append(peloss_list)
                pe_seriesloss_l.append(sum(peloss_list))
# .............................................................................................................

            # CE strikes for option pain
            dfsmall_ce_inv = dfsmall_ce.copy().sort_values('STRIKE_PR', axis=0, ascending=False, inplace=False,
                                                    kind='quicksort', na_position='last')
            celoss_1st = []
            for c in range(0, len(dfsmall_ce)):
                # i = 2
                # print(dfsmall_pe.iloc[i]['STRIKE_PR'])
                celoss_i = dfsmall_ce_inv.iloc[c]['OPEN_INT'] * (100 * c)
                celoss_1st.append(celoss_i)
            denom_ca = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            demon_cb = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            loss_clen = len(celoss_1st)

            celoss_mainlist = []
            ce_seriesloss_l = [sum(celoss_1st)] #this is the main value we looking for

            for clo in range(0, loss_clen - 1):
                # clo = 0
                denom_cmain = [i / j for i, j in zip(denom_ca[clo:], demon_cb[:-(clo + 1)])]
                celoss_list = [i / j for i, j in zip(celoss_1st[clo + 2:], denom_cmain)]
                celoss_mainlist.append(celoss_list)
                ce_seriesloss_l.append(sum(celoss_list))

            ce_seriesloss_l.reverse() # reverse sort order

            # calculate net loss for CE and PE
            netloss_list = [i + j for i, j in zip(pe_seriesloss_l, ce_seriesloss_l)]
            df_pain =pd.DataFrame({'Strikes':dfsmall_pe['STRIKE_PR'].to_list(),'Pain':netloss_list})

            df_pain['Mp_strike'] = np.where(df_pain['Pain'] == df_pain['Pain'].min(),df_pain['Strikes'],0)
            max_pain = df_pain['Mp_strike'].max()
            "#for plotting max pain along with IVs per strike"
            df_pain['CE_IV']= dfsmall_ce['iv']
            df_pain['PE_IV']= dfsmall_pe['iv']
            #......................................................................................................
            "Calculate pcr open interest & pcr weighted"
            pcroi = round(dfsmall_pe['OPEN_INT'].sum() / dfsmall_ce['OPEN_INT'].sum(), 2)
            pcrwt = round(dfsmall_pe['VAL_INLAKH'].sum() / dfsmall_ce['VAL_INLAKH'].sum(), 2)

            "Calculate most active CE for a day (max change in OI) and highest CE OI for series"
            rep = dfsmall_ce['CHG_IN_OI'].abs()
            rep = rep.astype('float64')
            valu = rep.idxmax()
            activecall = dfsmall_ce.iloc[valu]['STRIKE_PR']
            activecalloi = dfsmall_ce.iloc[valu]['OPEN_INT']
            ceiv_mean = round(dfsmall_ce['iv'].mean(), 2)

            "Calculate most active PE for a day (max change in OI) and highest PE OI for the series"
            rep_pe = dfsmall_pe['CHG_IN_OI'].abs()
            rep_pe = rep_pe.astype('float64')
            valu_pe = rep_pe.idxmax()
            activeput = dfsmall_pe.iloc[valu_pe]['STRIKE_PR']
            activeputoi = dfsmall_pe.iloc[valu_pe]['OPEN_INT']
            peiv_mean = round(dfsmall_pe['iv'].mean(), 2)

            repmx = dfsmall_ce['OPEN_INT'].abs()
            repmx = repmx.astype('float64')
            valumx = repmx.idxmax()
            activecallmx = dfsmall_ce.iloc[valumx]['STRIKE_PR']
            activecalloimx = dfsmall_ce.iloc[valumx]['OPEN_INT']

            rep_mxpe = dfsmall_pe['OPEN_INT'].abs()
            rep_mxpe = rep_mxpe.astype('float64')
            valu_mxpe = rep_mxpe.idxmax()
            activeputmx = dfsmall_pe.iloc[valu_mxpe]['STRIKE_PR']
            activeputoimx = dfsmall_pe.iloc[valu_mxpe]['OPEN_INT']

#..........................................................................................
            """
            Now we gonna compare today's values with historical values (I have added historical data)
            From here on run this file daily after 12.00 AM IST so it downloads prev days bhavcopy
            Why prev day instead of current day? Well NSE sometimes upload bhavcopy very late so in such
            cases script might download the same bhavcopy
            In case, if you fail to download, then adjust dayback=-1, 
            for instance for day before yesterday dayback=-2
            You can use that in loop to download all historical data as well
            """
            coi = (root + 'CE.txt')
            poi = (root + 'PE.txt')
            pcrw = (root + 'pcrw.txt')
            pcroi_file = (root + 'pcroi.txt')
            peiv_file = (root + 'peiv.txt')
            ceiv_file = (root + 'ceiv.txt')
            activece_file = (root + 'activece_strike.txt')
            activepe_file = (root + 'activepe_strike.txt')
            activeceoi_file = (root + 'activece_oi.txt')
            activepeoi_file = (root + 'activepe_oi.txt')
            nffile = root + 'Nifty4options.txt'

            "# chg pcroi"
            dfpcroi = pd.read_csv(pcroi_file)
            pcroi_prev = dfpcroi.iloc[-1][3]
            pcroi_chg = round(float(pcroi) - float(pcroi_prev), 2)
            "# chg pcr wt"
            t2 = pd.read_csv(pcrw, sep=",")
            pcr1 = t2.iloc[-1][3]
            pcr_wt_ch = pcrwt - pcr1
            # chg ivs for pe and ce
            dfpeiv = pd.read_csv(peiv_file, header=None)
            peiv_prev = dfpeiv.iloc[-1][3]
            peiv_chg = round(float(peiv_mean) - float(peiv_prev), 2)
            dfceiv = pd.read_csv(ceiv_file,header=None)
            ceiv_prev = dfceiv.iloc[-1][3]
            ceiv_chg = round(float(ceiv_mean) - float(ceiv_prev), 2)

            "#iv rank calculations"
            cutoff = 75 # max historical period
            dfceiv = dfceiv.tail(cutoff)
            dfpeiv = dfpeiv.tail(cutoff)
            #todo: append current values so rank wont be negative below
            dtx = dt_1.strftime("%Y%m%d")

            dfpeiv_current = pd.DataFrame(['PEIV', dtx, peiv_mean, peiv_mean, peiv_mean, peiv_mean]).transpose()
            dfceiv_current = pd.DataFrame(['CEIV', dtx, ceiv_mean, ceiv_mean, ceiv_mean, ceiv_mean]).transpose()
            dfpeiv_all = pd.concat([dfpeiv,dfpeiv_current],axis=0)
            dfceiv_all = pd.concat([dfceiv, dfceiv_current], axis=0)
            dfpeiv_all = dfpeiv_all.reset_index()
            dfceiv_all = dfceiv_all.reset_index()
            dfpeiv_all[4] = pd.to_numeric(dfpeiv_all[4])
            peiv_rank = 100*((peiv_mean - dfpeiv_all[4].min())/(dfpeiv_all[4].max() - dfpeiv_all[4].min()))
            dfceiv_all = dfceiv_all.dropna()
            dfceiv_all[4] = pd.to_numeric(dfceiv_all[4])
            ceiv_rank = 100*((ceiv_mean - dfceiv_all[4].min())/(dfceiv_all[4].max() - dfceiv_all[4].min()))
            "# iv percentile calculations"
            dfceiv_all['low_close'] = np.where(dfceiv_all[4]<ceiv_mean,1,0)
            ceiv_percentile = 100*(dfceiv_all['low_close'].sum()/cutoff)

            dfpeiv_all['low_close'] = np.where(dfpeiv_all[4]<peiv_mean,1,0)
            peiv_percentile = 100*(dfpeiv_all['low_close'].sum()/cutoff)

            "# ce unwinding"
            list_ce_unwind = (dfsmall_ce[dfsmall_ce['CHG_IN_OI'] < 0]).STRIKE_PR.to_list()
            list_pe_unwind = (dfsmall_pe[dfsmall_pe['CHG_IN_OI'] < 0]).STRIKE_PR.to_list()


            "# list of top 20 futures chnage in OI with scenarios"
            df_no_nf = df1[df1['OPTION_TYP'] == 'XX']
            # df_no_bnf = df_no_nf[df_no_nf['SYMBOL'] != 'BANKNIFTY']
            df_no_nf_current = df_no_nf.copy()[df_no_nf['EXPIRY_DT'] == expirydate]
            df_no_bnf_current = df_no_nf_current.sort_values('VAL_INLAKH', ascending=False)
            df_active10 = df_no_bnf_current.head(20)
            long_buildup_toplist = df_active10[(df_active10['CHG_IN_OI'] >= 0) &
                                               (df_active10['CLOSE'] >= df_active10['OPEN'])].SYMBOL.to_list()
            short_buildup_toplist = df_active10[(df_active10['CHG_IN_OI'] >= 0) &
                                                (df_active10['CLOSE'] < df_active10['OPEN'])].SYMBOL.to_list()
            short_cover_toplist = df_active10[(df_active10['CHG_IN_OI'] < 0) &
                                              (df_active10['CLOSE'] >= df_active10['OPEN'])].SYMBOL.to_list()

            long_liquid_toplist = df_active10[(df_active10['CHG_IN_OI'] < 0) &
                                              (df_active10['CLOSE'] < df_active10['OPEN'])].SYMBOL.to_list()

            long_sum =len(long_buildup_toplist)
            short_sum = len(short_buildup_toplist)
            longliq_sum = len(long_liquid_toplist)
            shortcover_sum = len(short_cover_toplist)
            ceunwind_sum = len(list_ce_unwind)
            peunwind_sum = len(list_pe_unwind)

            "# Now update current calculations to historical file"
            timeindex = dt_1.strftime("%H:%M:%S")
            #dateindex =dt_1.strftime("%Y%m%d,%H:%M:%S") # for Niftyf backward compatibility date index is date,time
            # dataframe(df) nf 4 (for) option 'o'
            df_nf4o = pd.DataFrame(['NiftyF', dtx, timeindex, nifty_o, nifty_h, nifty_l, nifty_price, nifty_v]).transpose()
            df_nf4o.to_csv(nffile, mode='a', index=False, header=False)

            df_pcroi = pd.DataFrame(['PCROI', dtx, pcroi, pcroi, pcroi, pcroi]).transpose()
            df_pcroi.to_csv(root + 'pcroi.txt', mode='a', index=False, header=False)

            df_peiv = pd.DataFrame(['PEIV', dtx, peiv_mean, peiv_mean, peiv_mean, peiv_mean]).transpose()
            df_peiv.to_csv(root + 'peiv.txt', mode='a', index=False, header=False)

            df_ceiv = pd.DataFrame(['CEIV', dtx, ceiv_mean, ceiv_mean, ceiv_mean, ceiv_mean]).transpose()
            df_ceiv.to_csv(root + 'ceiv.txt', mode='a', index=False, header=False)

            df_activece_f = pd.DataFrame(
                ['Active_CEstrike', dtx, activecallmx, activecallmx, activecallmx, activecallmx]).transpose()
            df_activece_f.to_csv(activece_file, mode='a', index=False, header=False)

            df_activepe_f = pd.DataFrame(
                ['Active_PEstrike', dtx, activeputmx, activeputmx, activeputmx, activeputmx]).transpose()
            df_activepe_f.to_csv(activepe_file, mode='a', index=False, header=False)

            df_activeceoi_f = pd.DataFrame(
                ['Active_CEOI', dtx, activecalloimx, activecalloimx, activecalloimx, activecalloimx]).transpose()
            df_activeceoi_f.to_csv(activeceoi_file, mode='a', index=False, header=False)

            df_activepeoi_f = pd.DataFrame(
                ['Active_PEOI', dtx, activeputoimx, activeputoimx, activeputoimx, activeputoimx]).transpose()
            df_activepeoi_f.to_csv(activepeoi_file, mode='a', index=False, header=False)

            df_CE = pd.DataFrame(['CE', dtx, activecalloi, activecalloi, activecalloi, activecalloi]).transpose()
            df_CE.to_csv(coi, mode='a', index=False, header=False)

            df_PE = pd.DataFrame(['PE', dtx, activeputoi, activeputoi, activeputoi, activeputoi]).transpose()
            df_PE.to_csv(poi, mode='a', index=False, header=False)

            df_pcrwr = pd.DataFrame(['pcrw', dtx, pcrwt, pcrwt, pcrwt, pcrwt]).transpose()
            df_pcrwr.to_csv(pcrw, mode='a', index=False, header=False)

            "#NFDaily, pcr oi, most active CE OI chg, most active CE OI chg daily history, index to datetime and make dfall"

            dfnf = pd.read_csv(root + 'Nifty4options.txt', header=None)
            dfnf.columns = ['symbol', 'date', 'time', 'o', 'h', 'l', 'c', 'v']
            dfnf['date'] = pd.to_datetime(dfnf['date'], format='%Y%m%d')
            dfnf = dfnf.set_index('date', drop=False, inplace=False)

            dfpcr = pd.read_csv(root + 'pcroi.txt', header=None)
            my_columns = ['symbol', 'date', 'o', 'h', 'l', 'c']
            dfpcr.columns = my_columns # ['symbol', 'date', 'o', 'h', 'l', 'c']
            dfpcr['date'] = pd.to_datetime(dfpcr['date'], format='%Y%m%d')
            dfpcr = dfpcr.set_index('date', drop=False, inplace=False)

            dfhybrid = dfnf.merge(dfpcr['c'], left_index=True, right_index=True, how='inner')
            dfhybrid = dfhybrid[['c_x', 'v', 'c_y']]
            dfhybrid.columns = ['NF_Close', 'Volume', 'PCR_OI']

            dfce = pd.read_csv(root + 'ceiv.txt', header=None)
            dfce.columns = my_columns # ['symbol', 'date', 'o', 'h', 'l', 'c']
            dfce['date'] = pd.to_datetime(dfce['date'], format='%Y%m%d')
            dfce = dfce.set_index('date', drop=False, inplace=False)

            dfpe = pd.read_csv(root + 'peiv.txt', header=None)
            dfpe.columns = my_columns # ['symbol', 'date', 'o', 'h', 'l', 'c']
            dfpe['date'] = pd.to_datetime(dfpe['date'], format='%Y%m%d')
            dfpe = dfpe.set_index('date', drop=False, inplace=False)

            dfcepe = dfce.merge(dfpe['c'], left_index=True, right_index=True, how='inner')
            dfcepe = dfcepe[['c_x', 'c_y']]
            dfcepe.columns = ['CE_IV', 'PE_IV']

            dfall = dfhybrid.merge(dfcepe[['CE_IV', 'PE_IV']], left_index=True, right_index=True, how='inner')

            "# let's plot using plotly "

            import plotly.graph_objs as go
            from plotly.subplots import make_subplots
            from plotly.offline import plot
            import plotly.express as px

            # split the list if list len > 7
            if len(short_buildup_toplist) >4:
                short_buildup_toplist.insert(3, '<br />')
            if len(short_buildup_toplist) >7:
                short_buildup_toplist.insert(7, '<br />')
            if len(short_buildup_toplist) >12:
                short_buildup_toplist.insert(12, '<br />')

            if len(long_buildup_toplist) >4:
                long_buildup_toplist.insert(3, '<br />')
            if len(long_buildup_toplist) >7:
                long_buildup_toplist.insert(7, '<br />')
            if len(long_buildup_toplist) >12:
                long_buildup_toplist.insert(12, '<br />')

            if len(long_liquid_toplist) >4:
                long_liquid_toplist.insert(3, '<br />')
            if len(long_liquid_toplist) >7:
                long_liquid_toplist.insert(7, '<br />')
            if len(long_liquid_toplist) >12:
                long_liquid_toplist.insert(12, '<br />')

            if len(short_cover_toplist) >4:
                short_cover_toplist.insert(3, '<br />')
            if len(short_cover_toplist) >7:
                short_cover_toplist.insert(7, '<br />')
            if len(short_cover_toplist) >12:
                short_cover_toplist.insert(12, '<br />')

            if len(list_ce_unwind) >4:
                list_ce_unwind.insert(3, '<br />')
            if len(list_ce_unwind) >7:
                list_ce_unwind.insert(7, '<br />')
            if len(list_ce_unwind) >12:
                list_ce_unwind.insert(12, '<br />')
            if len(list_pe_unwind) >4:
                list_pe_unwind.insert(3, '<br />')
            if len(list_pe_unwind) >7:
                list_pe_unwind.insert(7, '<br />')
            if len(list_pe_unwind) >12:
                list_pe_unwind.insert(12, '<br />')

            "#we are adding commentary on graph for easy reading all the calculation we have done so far"
            commentary_text = ('<br />' +
                               'Date:' + str(
                        dtx) + '<br />' + 'Series Expiry:' +str(expirydate)+ '<br /><br />' +
                               'For 20 highest traded futures:'+'<br />'+'Long Buildup:' +
                               '('+str(long_sum)+')+✔️'+
                               '<br />' + str(
                        long_buildup_toplist) + '<br />' + '...........' + '<br />' +
                               'Short Buildup:'+'(' +str(short_sum) +')'+'\u274C'+ '<br />' +
                               str(short_buildup_toplist) + '<br />' + '---------' + '<br />' +
                               'Long Liquidation:' +'('+str(longliq_sum) +')'+u'\u26D4'+ '<br />' +
                               str(long_liquid_toplist) + '<br />' + '----------' + '<br />' +
                               'Short Covering:'+'('+str(shortcover_sum)+')' +u'\u23EB'+ '<br />' + str(
                        short_cover_toplist) + '<br />' +
                               '------------------------------------------------------' +
                               '<br />' +'Nifty Options:'+'<br />'+'strike range considered by the algo'+ '<br />' +
                               str(roundp - 500)+'-'+ str(roundp + 600)
                               + '<br /><br />' +'x50 strikes are skipped eg.'+str(roundp+50)+'<br /><br />'+
                               'Call Unwinding:' + '('+str(ceunwind_sum)+')+✔️'+
                               '<br />' + str(
                        list_ce_unwind) + '<br />' + '------------' + '<br />' +
                               'Put Unwinding:' +'('+str(peunwind_sum)+')'+'\u274C'+'<br />' + str(
                        list_pe_unwind)+'<br />'+'PEIV_%tile* ' + str(round(peiv_percentile,2)) + ' PEIV_Rank* ' +
                               str(round(peiv_rank,2)) +'<br />'+'CEIV_%tile* ' + str(round(round(ceiv_percentile,2))) +
                               ' CEIV_Rank* ' + str(round(ceiv_rank,2))
                               )

            dfall = dfall.dropna()
            dfall = dfall.tail(20)
            dfall['CE_IV'] = dfall.CE_IV.astype(float)
            dfall['PE_IV'] = dfall.PE_IV.astype(float)

            # oimin = (min([dfall.PE_IV.min(), dfall.CE_IV.min()])) * 4
            oimax = (max([dfall.PE_IV.max(), dfall.CE_IV.max()])) * 4

            rangeh = dfall.NF_Close.max()
            rangel = dfall.NF_Close.min()
            xmax = max(rangeh, activecallmx)
            xmin = min(rangel, activeputmx)

            dfall['date'] = pd.to_datetime(dfall.index,format('Y-m-d'))
            dfall['date'] = pd.to_datetime(dfall['date'],
                                           format='%Y-%m-%d', infer_datetime_format=True).dt.strftime('%Y-%m-%d')
            #todo: plot
            subfig = make_subplots(rows=2, cols=1, start_cell="top-left",
                                   subplot_titles=("PCR_vs_NF", "MaxPain_vs_IVs"),
                                   specs=[[{"secondary_y": True}],
                                          [{"secondary_y": True}]])

            subfig.add_trace(go.Scatter(x=dfall.date, y=dfall['NF_Close'], mode='lines+markers',
                                        name='NiftyF', line=dict(width=3, color='cyan'),
                                        showlegend=False),
                             secondary_y=False,row=1,col=1
                             )
            subfig.add_trace(
                go.Scattergl(x=[dfall.date.iloc[-1]], y=[dfall.iloc[-1]['NF_Close']], mode="text", text='Nifty_F',
                             textposition="top right",
                             showlegend=False, textfont=dict(family="verdana", size=12, color='cyan')),row=1,col=1)

            subfig.layout.xaxis.type = 'category'
            subfig.add_trace(go.Scatter(x=dfall.date, y=dfall['PCR_OI'], mode='lines+markers',
                                        name='PCR_OI', line=dict(width=1, color='yellow'), showlegend=False),
                             secondary_y=True,row=1, col=1
                             )
            subfig.add_trace(
                go.Scattergl(x=[dfall.date.iloc[-1]], y=[dfall.iloc[-1]['PCR_OI']], mode="text", text='PCR_OI',
                             textposition="bottom right",
                             showlegend=False, textfont=dict(family="verdana", size=12, color='yellow')),secondary_y=True,
                row=1,col=1)

            subfig.add_trace(go.Bar(x=[dfall.date.iloc[-1]], y=[dfall.date[-1]], marker=dict(color='white'), yaxis='y3',
                                    name='<br /><br />F&O Summary' + '<br />' + commentary_text),secondary_y=True,row=1,col=1)
            subfig.add_trace(
                go.Scattergl(x=[dfall.date[1]], y=[activeputmx], mode="text", text='PE_Max_OI: ' +
                                                                                    str(activeputmx),
                             textposition="top left",
                             showlegend=False, textfont=dict(family="verdana", size=12, color='white')),row=1,col=1)

            subfig.add_trace(
                go.Scattergl(x=[dfall.date.iloc[1]], y=[activecallmx], mode="text", text='CE_Max_OI: ' +
                                                                                     str(activecallmx),
                             textposition="bottom left",
                             showlegend=False, textfont=dict(family="verdana", size=12, color='white')),row=1,col=1)

            subfig.add_trace(go.Bar(x=df_pain.Strikes, y=df_pain['Pain'],
                                    marker=dict(color='magenta',opacity=0.2),showlegend=False,yaxis='y4',
                                    name='Max_Pain'),secondary_y=True,row=2,col=1)

            subfig.add_trace(
                go.Scattergl(x=[max_pain], y=[df_pain['Pain'].min()*1.25], mode="text", text='Max_Pain',
                             textposition="top center",
                             showlegend=False, textfont=dict(family="verdana", size=14, color='magenta')),secondary_y=True,
                row=2,col=1)

            subfig.add_trace(go.Scatter(x=df_pain.Strikes, y=df_pain['CE_IV'], mode='lines+markers',
                                        name='CE_IV', line=dict(width=3, color='cyan'),showlegend=False),
                             secondary_y=False,row=2,col=1
                             )
            subfig.add_trace(
                go.Scattergl(x=[df_pain.iloc[-1]['Strikes']], y=[df_pain.iloc[-1]['CE_IV']], mode="text", text='CE_IV',
                             textposition="top right",
                             showlegend=False, textfont=dict(family="verdana", size=12, color='cyan')),row=2,col=1)

            # # subfig.layout.xaxis.type = 'category'
            subfig.add_trace(go.Scatter(x=df_pain.Strikes, y=df_pain['PE_IV'], mode='lines+markers',
                                        name='PE_IV', line=dict(width=1, color='yellow'), showlegend=False),
                             secondary_y=False,row=2, col=1
                             )
            subfig.add_trace(
                go.Scattergl(x=[df_pain.iloc[-1]['Strikes']], y=[df_pain.iloc[-1]['PE_IV']], mode="text", text='PE_IV',
                             textposition="bottom right",
                             showlegend=False, textfont=dict(family="verdana", size=12, color='yellow')),row=2,col=1)


            subfig.update_xaxes(showline=True, color='white', showgrid=False,
                                type = 'category',tickangle=45, row=1, col=1)
            subfig.update_xaxes(showline=True, color='white', showgrid=False,tickformat='d',
                                dtick=100,tickangle=45, row=2, col=1)

            # Update yaxis properties
            subfig.update_yaxes(showline=True, color='white', showgrid=False, row=1, col=1)
            subfig.update_yaxes(showline=True, color='white', showgrid=False, row=1, col=1)
            subfig.update_yaxes(showline=True, color='white', showgrid=False, row=2, col=1)
            subfig.update_yaxes(showline=True, color='white', showgrid=False,
                                row=2, col=1)
            subfig.update_layout(paper_bgcolor='black', plot_bgcolor='black', title='Option_Depth',
                                 title_font=dict(size=18, color='white'),
                                 height=1000, width=1900,
                                 xaxis2=dict(title='Strikes',titlefont=dict(color='white'),
                                             ),
                                 yaxis=dict(title='Nifty_F',titlefont=dict(color='cyan'),
                                            range=[xmin - 10, xmax + 00]), yaxis_tickformat='d',
                                 yaxis4=dict(title='Max_Pain',titlefont=dict(color='magenta'),
                                             range=[0, df_pain['Pain'].max() * 2]),
                                 yaxis3=dict(showline=True,
                                              title='CE_PE_IV',
                                              titlefont=dict(
                                                  color="gray"
                                              ),
                                              tickfont=dict(
                                                  color="white"
                                              ),anchor="free"),
                                             legend=dict(font=dict(color='White', size=14)))
            plot(subfig, auto_open=True)


            # scope = PlotlyScope()
            # pic_url = root+"options.png"
            # with open(pic_url, "wb") as f:
            #     f.write(scope.transform(subfig, format="png"))

            subfig.write_image(root + "niftyoptios.jpeg")


            # subfig.show()

            print('success bhav')



    except Exception as e:
        root =path
        todays_date = date_string('%d%m%Y')
        print(str(e))
        with open(root +'failed.txt', 'a') as f:
            f.write('For date ' + todays_date + ' a1bhav_fo ' + '  ' + str(e) + '\n')

    finally:
        pass
    return


bhav_options(dayback=-1)
