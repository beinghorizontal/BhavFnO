# from def_custom_tabulate import custom_tabulate
# from tabulate import tabulate
from def_get_options import get_options
import numpy as np
# from def_custom_tabulate import custom_tabulate
import pandas as pd
from screeninfo import get_monitors
import datetime

" uncomment this if you need backfill, for running first time it is must,"
#.................................................................................************........
# df_list = []
# dfPain_list = []
# # # C keep the path same for using it regularly
# fnoFilePath = 'd:/demos/storage/fno.csv'
# mxpainFilePath = 'd:/demos/storage/mxpain.csv'
# #
# i = 0
# for i in range(0, 35):
#     try:
#         day_back = i  # day_back = 1 = yesDay, 0 = Today
#         list_df_pain = get_options(dayback=day_back)
#         df = list_df_pain[0]
#         dfPain = list_df_pain[1]
#         if len(df) != 0:
#             df_list.append(df)
#             dfPain['date'] = df['TimeIndex'].iloc[0]
#             dfPain_list.append(dfPain)
#     except Exception as s:
#         print(s)
#
# df_final = pd.concat(df_list)
# df_final = df_final.reset_index(drop=True)
# df_final = df_final.sort_index(ascending=False)
# dfpainMerge = pd.concat(dfPain_list)
# df_final.to_csv(fnoFilePath, index=False, mode='w')
# dfpainMerge.to_csv(mxpainFilePath, index=False, mode='w')  # C append new files and save to path

#..........*********************************************************........................................,,,,,


#day_back = 0  # day_back = 1 = yesDay, 0 = Today
def getDdata(day_back=0):
    fnoFilePath = 'd:/demos/storage/fno.csv'
    mxpainFilePath = 'd:/demos/storage/mxpain.csv'

    list_df_pain = get_options(dayback=day_back)
    df = list_df_pain[0]
    dfPain = list_df_pain[1]
    dfPain['date'] = df['TimeIndex'].iloc[0]

    dfHist = pd.read_csv(fnoFilePath)
    dfpainHist = pd.read_csv(mxpainFilePath)

    df_final = pd.concat([dfHist, df])
    df_final = df_final.reset_index(drop=True)
    dfpainMerge = pd.concat([dfPain, dfpainHist])
    dfpainMerge = dfpainMerge.reset_index(drop=True)
    if day_back == 0:
        df_final.to_csv(fnoFilePath, index=False, mode='w')
        dfpainMerge.to_csv(mxpainFilePath, index=False, mode='w')  # C append new files and save to path
    return df_final, dfpainMerge

def run_chart(dayback=0):

    dfall = getDdata(day_back=dayback)
    # df_final = pd.read_csv(fnoFilePath)
    # dfpainMerge = pd.read_csv(mxpainFilePath)
    df_final = dfall[0]
    dfpainMerge = dfall[1]
    filterDate_datetime = datetime.datetime.now() - datetime.timedelta(dayback)
    filterDate = datetime.datetime.now() - datetime.timedelta(dayback)
    filterDate = filterDate.strftime('%Y%m%dT')
    displayDate = filterDate_datetime.strftime('%Y/%m/%d')

    dfPain_final = dfpainMerge[dfpainMerge['date']==filterDate]
    # print(custom_tabulate(dfPain_final))
    cutoff = len(df_final)
    # print(custom_tabulate(dfPain_final2))

    dfPain_final2 = df_final[df_final['TimeIndex'] == filterDate]
    if len(dfPain_final2) >= 1:
        ceIvLast = dfPain_final2.iloc[-1]['CEIV_Mean']
        peIvLast = dfPain_final2.iloc[-1]['PEIV_Mean']
        peIvRank = 100 * ((peIvLast - df_final['PEIV_Mean'].min()) / (df_final['PEIV_Mean'].max() - df_final['PEIV_Mean'].min()))
        ceIvRank = 100 * ((ceIvLast - df_final['CEIV_Mean'].min()) / (df_final['CEIV_Mean'].max() - df_final['CEIV_Mean'].min()))

        # C iv percentile calculations
        df_final['ceIvLow'] = np.where(df_final['CEIV_Mean'] < ceIvLast, 1, 0)
        ceiv_percentile = 100 * (df_final['ceIvLow'].sum() / cutoff)

        df_final['peIvLow'] = np.where(df_final['PEIV_Mean'] < peIvLast, 1, 0)

        peiv_percentile = 100 * (df_final['peIvLow'].sum() / cutoff)
    else:
        peIvRank = 0
        ceIvRank = 0
        ceiv_percentile = 0
        peiv_percentile = 0

    import plotly.graph_objs as go
    from plotly.subplots import make_subplots
    from plotly.offline import plot


    # fig = {}
    fig = make_subplots(rows=2, cols=3,subplot_titles=[''],vertical_spacing=0.1,horizontal_spacing=0.1,
                        specs=[[{"secondary_y": True}, {"secondary_y": False},{"secondary_y": True}],
                               [{"secondary_y": True}, {"secondary_y": True},{"secondary_y": True}]])


    title_font_style = dict(color='white', size=16, family='Arial')
    fig.update_layout(title_font=title_font_style)

    if len(dfPain_final2) >= 1:
        long = dfPain_final2.iloc[-1]['Long_Sum']
        longLiq = dfPain_final2.iloc[-1]['LongLiq_Sum']
        short = dfPain_final2.iloc[-1]['Short_Sum']
        shorCover = dfPain_final2.iloc[-1]['ShortCover_Sum']
        ceUnwind = dfPain_final2.iloc[-1]['CE_Unwind_Sum']
        peUnwind = dfPain_final2.iloc[-1]['PE_Unwind_Sum']
    else:
        long = 0
        longLiq = 0
        short = 0
        shorCover = 0
        ceUnwind = 0
        peUnwind = 0


    colors = ['green', 'orange', 'red', 'blue', 'forestgreen', 'pink']

    fig.add_trace(go.Bar(x=['long', 'LongLiq','short','ShortCover','CE Unwind', 'PE Unwind'],
                         y=[long,longLiq,short,shorCover,ceUnwind,peUnwind],
                         name=f'<span style="{colors}:white"></span>',
                         marker=dict(color=colors),
                         ),
                  row=1, col=1)
    fig.update_xaxes(showline=True, color='white', showgrid=False,tickfont=dict(size=14),
                        type='category', tickangle=45, row=1, col=1)

    # C scatter plots for bullish and bearish stock futures ................... row 1, col 3......

    df_final['BearishSf'] = 0
    df_final['BearishSf'] = df_final['Short_Sum']*2 + df_final['LongLiq_Sum']  # C 0.5%lower wt for long liquidation[heuristic]
    df_final['BullishSf'] = 0
    df_final['BullishSf'] = df_final['Long_Sum'] + df_final['ShortCover_Sum']*2  # C higher weightage for short covering[heuristic]

    from sklearn.preprocessing import MinMaxScaler

    scaler = MinMaxScaler(feature_range=(3,5))
    df_final[['BearishSf']] = scaler.fit_transform(df_final[['BearishSf']])
    df_final[['BullishSf']] = scaler.fit_transform(df_final[['BullishSf']])

    fig.add_trace(go.Scatter(x=df_final.TimeIndex, y=df_final['Nifty_Close'],mode='lines+markers',
                             name='<span style="color:cyan">Nifty Futures</span>',
                             line=dict(width=3, color='cyan')),secondary_y=False,col=3,row=1)

    fig.update_xaxes(rangeslider=dict(visible=False), row=1, col=3)  # Disable rangeslider

    fig.update_xaxes(showline=True, color='white', showgrid=False,tickfont=dict(size=7),
                        type='category', tickangle=45, row=1, col=3)

    fig.add_trace(go.Scatter(x=df_final.TimeIndex, y=df_final['MaxPain'],mode='markers+lines',
                             name='<span style="color:gray">Max_Pain</span>',
                             line=dict(width=1, color='gray',dash='dash'),marker=dict(size=3)),
                  secondary_y=False,col=3,row=1)

    fig.add_trace(go.Scatter(x=df_final.TimeIndex, y=df_final['MX_CE'],mode='lines+markers',
                             name='<span style="color:red">ActiveCE</span>',
                             line=dict(width=1, color='red',dash='dash'),marker=dict(size=3)),
                  secondary_y=False,col=3,row=1)

    fig.add_trace(go.Scatter(x=df_final.TimeIndex, y=df_final['MX_PE'],mode='lines+markers',
                             name='<span style="color:limegreen">ActivePE</span>',
                             line=dict(width=1, color='limegreen',dash='dash'),marker=dict(size=3)),
                  secondary_y=False,col=3,row=1)

    # fig.update_xaxes(showgrid=False,row=1,col=3,type='category',color='white')
    fig.add_trace(go.Bar(x=df_final.TimeIndex, y=df_final['PCR_OI'],
                             name='<span style="color:magenta">PCR_OI</span>',
                             marker=dict(color='magenta')),secondary_y=False,col=3,row=2)

    fig.add_trace(
        go.Bar(
            x=df_final['TimeIndex'],
            y=df_final['PCR_WT'],
            name=f'<span style="color:cyan">PCR_WT</span>',
            marker=dict(color='cyan'),
        showlegend=True),
    secondary_y=False,col=3,row=2)

    fig.add_trace(go.Scatter(x=df_final['TimeIndex'], y=df_final['BullishSf'],mode='markers',
                         name=f'<span style="color:limegreen">Bullish stock Fut</span>',
                         marker=dict(color='limegreen'),
                         ),
                  row=2, col=3,secondary_y=False)

    fig.add_trace(go.Scatter(x=df_final['TimeIndex'], y=df_final['BearishSf'],mode='markers',
                         name=f'<span style="color:hotpink">Bearish stock Fut</span>',
                         marker=dict(color='hotpink'),
                         ),
                  row=2, col=3,secondary_y=False)

    # fig.update_yaxes(row=2, col=3,tickformat='d',
    #                  secondary_y=True,showgrid=False, color='white')
    fig.update_yaxes(row=2, col=3,tickformat='d',range=[0,7],
                     secondary_y=False,showgrid=False, color='white')

    fig.update_xaxes(showgrid=False, color='white',col=3,row=2)

    # fig.update_yaxes(title_text='Put/Call OI Ratio', row=1, col=1, secondary_y=True)

    # Row 1, Col 2 - IV Rank and Percentile

    # C ........................ row 1 col 2 ...................................................

    fig.add_trace(go.Bar(x=['IV Rank', 'IV Percentile'], y=[peIvRank, peiv_percentile],
                         name=f'<span style="color:pink">PE: IV Rank, Percentile</span>',
                         marker=dict(color='pink'),
                         ),
                  row=1, col=2)

    fig.add_trace(go.Bar(x=['IV Rank', 'IV Percentile'], y=[ceIvRank, ceiv_percentile],
                         name=f'<span style="color:blue">CE: IV Rank, Percentile</span>',
                         marker=dict(color='blue'),
                         ),
                  row=1, col=2)
    fig.update_xaxes(showline=True, color='white', showgrid=False,tickfont=dict(size=14),
                        type='category', tickangle=45, row=1, col=2)



    fig.add_annotation(
        text=f"Day's Option Snapshot {displayDate}",
        xref='paper',
        yref='paper',
        x=0,
        y=1.05,
        showarrow=False,
        align='left',
    font=dict(color='teal')
    )
    periodStart = df_final.iloc[0]['TimeIndex']
    periodEnd = df_final.iloc[-1]['TimeIndex']

    fig.add_annotation(
        text=f'Historical Study: {periodStart} - {periodEnd}',
        xref='paper',
        yref='paper',
        x=1,
        y=1.05,
        showarrow=False,
        align='right',
    font=dict(color='teal')
    )


    fig.add_trace(go.Bar(x=dfPain_final.Strikes, y=dfPain_final['Pain'],
                            marker=dict(color='magenta', opacity=0.2),
                         showlegend=True, yaxis='y4',
                         name=f'<span style="color:magenta">Max Pain</span>',
                         ), secondary_y=True, row=2, col=1)
    # fig.update_layout(barmode='group')

    max_pain = dfPain_final['Mp_strike'].max()
    fig.add_trace(go.Scatter(x=dfPain_final.Strikes, y=dfPain_final['CE_IV'], mode='lines+markers',
                                name=f'<span style="color:cyan">CE_IV</span>',
                             line=dict(width=3, color='cyan'), showlegend=True),
                     secondary_y=False, row=2, col=1
                     )

    fig.update_yaxes(title_text='Max Pain', row=2, col=1, secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text='IVs', row=2, col=1, secondary_y=False, showgrid=False)

    fig.update_yaxes(row=2, col=1,tickformat='d', secondary_y=False)
    fig.update_yaxes(title_text="Chg_OIvsOI",row=2, col=2, secondary_y=True, showgrid=False)


    # # fig.layout.xaxis.type = 'category'
    fig.add_trace(go.Scatter(x=dfPain_final.Strikes, y=dfPain_final['PE_IV'], mode='lines+markers',
                                name=f'<span style="color:yellow">PE_IV</span>',
                             line=dict(width=1, color='yellow'), showlegend=True),
                     secondary_y=False, row=2, col=1
                     )

    fig.update_xaxes(showline=True, color='white', showgrid=False, tickformat='d',
                        dtick=100, tickangle=45, row=2, col=1)
    # Update yaxis properties
    fig.update_yaxes(showline=True, color='white', showgrid=False, row=1, col=1, range=[0.2,3],secondary_y=True)

    fig.update_yaxes(showline=True, color='white', showgrid=False, row=2, col=1)

    fig.add_trace(go.Bar(x=dfPain_final.Strikes, y=dfPain_final['ceCHG_IN_OI'],
                            marker=dict(color='magenta', opacity=0.2), showlegend=True,
                         name=f'<span style="color:magenta">CE Chane in OI</span>',
                                     ),
                     secondary_y=False, row=2, col=2)

    fig.add_trace(go.Bar(x=dfPain_final.Strikes, y=dfPain_final['peCHG_IN_OI'],
                            marker=dict(color='limegreen', opacity=0.2), showlegend=True,
                         name=f'<span style="color:limegreen">PE Change in OI</span>',
                                     ),
                     secondary_y=False, row=2, col=2)
    #
    fig.update_layout(barmode='group')

    fig.add_trace(go.Scattergl(x=dfPain_final['Strikes'], y=dfPain_final['ceOPEN_INT'],
                                  mode='lines+markers',
                                  name=f'<span style="color:red">Call OI</span>',
                                  line=dict(width=1, color='red'),
                                  showlegend=True, yaxis='y4'),
                     secondary_y=True, row=2, col=2)


    fig.add_trace(go.Scattergl(x=dfPain_final['Strikes'], y=dfPain_final['peOPEN_INT'],
                                  mode='lines+markers',
                                  name=f'<span style="color:green">Put OI</span>',
                               line=dict(width=1, color='green'),
                                  showlegend=True, yaxis='y4'),
                     secondary_y=True, row=2, col=2)


    fig.update_xaxes(showline=True, color='white', showgrid=False,
                        dtick=100, tickangle=45, row=2, col=2)

    fig.update_xaxes( showgrid=False, color='black', col=1,row=2)
    fig.update_xaxes(rangeslider=dict(visible=False), row=1, col=1)  # Disable rangeslider
    # Update subplot titles' font color and style

    # print(custom_tabulate(df_final))

    fig.update_yaxes( showgrid=False, color='white')


    # Get screen resolution
    monitor_index = 2
    monitors = get_monitors()
    chosen_monitor = monitors[monitor_index]
    screen_width = chosen_monitor.width
    screen_height = chosen_monitor.height

    fig.update_layout(paper_bgcolor='black', plot_bgcolor='black', height=int(screen_height * 0.7),
                         width=int(screen_width * 0.8),
                         title = '<a href="https://www.youtube.com/@quantext/featured">Youtube @quantext</a>',
                         showlegend=True, title_font=dict(size=12, color='white'),
                         uniformtext=dict(minsize=11, mode='hide'),
                         margin=dict(t=65, l=5, r=5, b=45)
                         )

    plot(fig)
""" If dayback = 0 then only it will add new data to the existing csv and rewrite the file else will run the function
without rewriting the csv. It is easy to see past data without adding duplicate lines in the historical csv
"""
run_chart(dayback=1)
# C to open last 7 days chart (including weekends)
# C note, during weekend Daily snapshot part will be blank
# for i in range(1,15):
#     run_chart(dayback=i)
