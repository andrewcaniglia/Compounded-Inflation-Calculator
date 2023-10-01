from concurrent.futures import ThreadPoolExecutor

import pandas as pd

#Works for most of the tables from usinflationcalculator.com
def make_usable(df):
    df=df.melt(id_vars='Year', var_name='Month', value_name='YoY')
    #Clean
    df.dropna(inplace=True)
    # #That's not a month
    df=df[df['Month']!='Ave']
    # #Make date usable
    df['Date']=df['Year'].astype('str')+df['Month']
    df['Date']=pd.to_datetime(df['Date'], format='%Y%b')
    #Gets rid of value that is just the date of the next CPI reading
    df=df[~df['YoY'].astype('str').str.contains('Avail.')][['Date', 'YoY']]
    df['YoY']=[float(x) for x in df['YoY']]
    df.rename(columns={'YoY': '1 Year'}, inplace=True)
    df.sort_values('Date', inplace=True, ignore_index=True)
    df.set_index('Date', inplace=True)
    return df

#Headline CPI
def process_mi(mi):
    return make_usable(mi)
    
#Core CPI
def process_ci(ci):
    ci.columns=ci.iloc[len(ci)-1]
    ci=ci[:-1]
    return make_usable(ci)

#Energy inflation
def process_ei(ei):
    ei.columns=ei.iloc[0]
    ei=ei[1:]
    return make_usable(ei)

#Gasoline
def process_ga(ga):
    ga.columns=ga.iloc[0]
    ga=ga[1:]
    ga.columns=ga.columns.str.capitalize()
    return make_usable(ga)

#Groceries
def process_gi(gi):
    gi.columns=gi.iloc[0]
    gi=gi[1:]
    return make_usable(gi)

#Food
def process_fi(fi):
    return make_usable(fi)

#Health Care
def process_hi(hi):
    hi.columns=hi.iloc[0]
    hi=hi[1:]
    return make_usable(hi)

#College
def process_co(co):
    co.columns=co.iloc[0]
    co=co[1:]
    co=co.melt(id_vars='Year', var_name='Month', value_name='YoY')
    #Clean
    huh=co[(co['Month']=='Jan')&(co['Year']=='1978')]['YoY'].values[0]
    co=co[co['YoY']!=huh]
    co.dropna(inplace=True)
    # # #That's not a month
    co=co[co['Month']!='Ave']
    # # #Make date usable
    co['Date']=co['Year'].astype('str')+co['Month']
    co['Date']=pd.to_datetime(co['Date'], format='%Y%b')
    #Final fix
    co=co[~co['YoY'].astype('str').str.contains('Avail.')][['Date', 'YoY']]
    co['YoY']=[float(x) for x in co['YoY']]
    co.rename(columns={'YoY':'1 Year'}, inplace=True)
    co.sort_values('Date', inplace=True, ignore_index=True)
    co.set_index('Date', inplace=True)
    return co

#Airline
def process_ai(ai):
    ai.columns=ai.iloc[0]
    ai=ai[1:]
    ai=ai[ai['Year'].astype('int')>=1970]
    return make_usable(ai)

#Matches url of the table with the prcoessing function for it
tasks = [
    ('https://www.usinflationcalculator.com/inflation/historical-inflation-rates/', process_mi),
    ('https://www.usinflationcalculator.com/inflation/united-states-core-inflation-rates/', process_ci),
    ('https://www.usinflationcalculator.com/inflation/energy-prices-gasoline-electricity-and-fuel-oil-2015-present/', process_ei),
    ('https://www.usinflationcalculator.com/inflation/gasoline-inflation-in-the-united-states/', process_ga),
    ('https://www.usinflationcalculator.com/inflation/average-prices-for-selected-grocery-store-items-2015-present/', process_gi),
    ('https://www.usinflationcalculator.com/inflation/food-inflation-in-the-united-states/', process_fi),
    ('https://www.usinflationcalculator.com/inflation/health-care-inflation-in-the-united-states/', process_hi),
    ('https://www.usinflationcalculator.com/inflation/college-tuition-inflation-in-the-united-states/', process_co),
    ('https://www.usinflationcalculator.com/inflation/airfare-inflation/', process_ai)
]
 
#Fetches processed table from its url
def fetch_and_process_data(task):
    url, processing_function = task
    df = pd.read_html(url)[0]
    return processing_function(df)

#Fetches all tables with multi-threading
def get_processed_data():
    with ThreadPoolExecutor() as executor:
        processed_data_list = list(executor.map(fetch_and_process_data, tasks))

    #Stores all tables in a dictionary
    data_sources = {
        'Headline CPI': processed_data_list[0],
        'Core CPI': processed_data_list[1],
        'Energy': processed_data_list[2],
        'Gas': processed_data_list[3],
        'Grocery': processed_data_list[4],
        'Food': processed_data_list[5],
        'Healthcare': processed_data_list[6],
        'College': processed_data_list[7],
        'Airline': processed_data_list[8]
    }
    
    return data_sources
    
data_sources= get_processed_data()
