import pandas as pd
import numpy as np
from google.oauth2 import service_account
import pandas_gbq
import matplotlib.pyplot as plt
from google.oauth2 import service_account
from google.cloud import bigquery
import sqlalchemy

directory = '/usr/local/airflow/dags/'

##############################################################################
# COVID19
##############################################################################

url='https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
df_covid = pd.read_csv(url,index_col=0,parse_dates=[0])
df_covid['category'] = 'covid'
df_covid = df_covid[['category','date','location','continent','new_cases','new_deaths']]
df_covid = df_covid.rename(columns={"new_cases":"tt_cases","new_deaths":"tt_deaths","location":"country"})

# Delete Continente NULL
df_covid_index_to_drop = df_covid[df_covid['continent'].isnull()].index
#df_covid_index_to_drop = df_covid[df_covid['continent']==''].index
df_covid.drop(df_covid_index_to_drop , inplace=True)

df_covid['tt_cases'].sum()
# Create dataframe to get continent
df_country_covid = df_covid[['country','continent']]
df_country_covid['country'] = df_covid['country'].str[:8]
df_country_covid.drop_duplicates(inplace=True)

# Gerar acumulado por dias
df_covid_date = df_covid['date'].dropna().drop_duplicates()
df_covid_date = pd.DataFrame(df_covid_date)
df_covid_date['contador_dia'] = 1
df_covid_date['contador_dia'] = df_covid_date['contador_dia'].cumsum()
df_covid = pd.merge(left=df_covid,right=df_covid_date,how='left',left_on='date',right_on='date')

# Marcação da origem da doença
df_covid['origem'] = np.logical_and(df_covid['contador_dia']==1, df_covid['tt_cases'] != 0)
df_covid['origem'] = np.where(df_covid['origem'] == False,0,1)

df_covid["tt_cases"].sum()
df_covid["tt_deaths"].sum()

#df_teste = df_covid[(df_covid.tt_cases < -10000)]

#df_covid_eua = df_covid[df_covid["country"]=="United States"]

# get countries with vaccinations data
#df_covid_new_vaccinations = df_covid[~df_covid["new_vaccinations"].isnull()]

#df_covid_cases = df_covid.iloc[:,[2,3,5,8]]
#df_covid_cases.dropna(inplace=True)


df_covid['date'] = pd.to_datetime(df_covid['date'])

df_covid_cases_boxplot = df_covid.dropna()

# tt cases negativos
df_covid[(df_covid.tt_cases < 0)].count()
# tt deaths negativos
df_covid[(df_covid.tt_deaths < 0)].count()
# outiliers tt_cases
plt.boxplot(df_covid.iloc[:,4],showfliers=True)
# outiliers tt_deaths
plt.boxplot(df_covid.iloc[:,5],showfliers=True)


df_covid_cases_outliers = df_covid[(df_covid.tt_cases < 0)]
df_covid_deaths_outliers = df_covid[(df_covid.tt_deaths < 0)]

df_covid_cases_outliers['date_dif'] = df_covid_cases_outliers['date'] - timedelta(days=7)
df_covid_deaths_outliers['date_dif'] = df_covid_deaths_outliers['date'] - timedelta(days=7)

df_covid_cases_outliers = pd.merge(left=df_covid_cases_outliers,right=df_covid[['date','country','tt_cases','tt_deaths']],how='left',left_on=['date_dif','country'],right_on=['date','country'])
df_covid_cases_outliers['tt_cases_y'] = np.where(df_covid_cases_outliers['tt_cases_y'] < 0,0,df_covid_cases_outliers['tt_cases_y'])
df_covid_cases_outliers['tt_deaths_y'] = np.where(df_covid_cases_outliers['tt_deaths_y'] < 0,0,df_covid_cases_outliers['tt_deaths_y'])

df_covid_deaths_outliers = pd.merge(left=df_covid_deaths_outliers,right=df_covid[['date','country','tt_cases','tt_deaths']],how='left',left_on=['date_dif','country'],right_on=['date','country'])
df_covid_deaths_outliers['tt_cases_y'] = np.where(df_covid_deaths_outliers['tt_cases_y'] < 0,0,df_covid_deaths_outliers['tt_cases_y'])
df_covid_deaths_outliers['tt_deaths_y'] = np.where(df_covid_deaths_outliers['tt_deaths_y'] < 0,0,df_covid_deaths_outliers['tt_deaths_y'])

df_covid_outliers = pd.concat([df_covid_cases_outliers,df_covid_deaths_outliers])

df_covid_outliers.drop_duplicates(inplace=True)

df_covid = pd.merge(left=df_covid,right=df_covid_outliers[['date_x','country','tt_cases_y','tt_deaths_y']],how='left',left_on=['date','country'],right_on=['date_x','country'])
df_covid['tt_cases'] = np.where(df_covid['tt_cases'] < 0,df_covid['tt_cases_y'],df_covid['tt_cases'])
df_covid['tt_deaths'] = np.where(df_covid['tt_deaths'] < 0,df_covid['tt_deaths_y'],df_covid['tt_deaths'])
# tratando os nan
df_covid['tt_cases'] = np.where(df_covid['tt_cases'].isnull(),0,df_covid['tt_cases'])
df_covid['tt_deaths'] = np.where(df_covid['tt_deaths'].isnull(),0,df_covid['tt_deaths'])

# tt cases negativos
df_covid[(df_covid.tt_cases < 0)].count()
# tt deaths negativos
df_covid[(df_covid.tt_deaths < 0)].count()

plt.boxplot(df_covid.iloc[:,4],showfliers=True)
# outiliers tt_deaths
plt.boxplot(df_covid.iloc[:,5],showfliers=True)

df_covid.drop(["date_x","tt_cases_y","tt_deaths_y"], axis=1, inplace=True)





##############################################################################
# EBOLA
##############################################################################

df_ebola = pd.read_csv(directory+'data/dataset_ebola.csv',sep=",")
#df_ebola['Indicator'].unique().tolist()
df_ebola['category'] = 'ebola'
df_ebola['continent'] = 'null'
df_ebola['tt_cases'] = df_ebola['value'].where(df_ebola['Indicator'] == 'Cumulative number of confirmed Ebola cases')
df_ebola['tt_deaths'] = df_ebola['value'].where(df_ebola['Indicator'] == 'Cumulative number of confirmed Ebola deaths')
df_ebola.columns=['indicator','country','date','value','category','continent','tt_cases','tt_deaths']
df_ebola = df_ebola.groupby(['category','date','country','continent'])['tt_cases','tt_deaths'].sum().reset_index()

# Alterar nomes de paises invalidos
df_ebola["country"] = df_ebola["country"].replace(['Liberia 2'],'Liberia')
df_ebola["country"] = df_ebola["country"].replace(['Guinea 2'],'Guinea')
df_ebola['country_merge'] = df_ebola['country'].str[:8]

# merge para classificar continent
df_ebola = pd.merge(left=df_ebola,right=df_country_covid,how='left',left_on='country_merge',right_on='country')
df_ebola = df_ebola.rename(columns={"country_x":"country","continent_y":"continent"})
df_ebola = df_ebola[["category","date","country","continent","tt_cases","tt_deaths"]]

# Gerar acumulado por dias
df_ebola_date = df_ebola['date'].dropna().drop_duplicates()
df_ebola_date = pd.DataFrame(df_ebola_date)
df_ebola_date['contador_dia'] = 1
df_ebola_date['contador_dia'] = df_ebola_date['contador_dia'].cumsum()
df_ebola = pd.merge(left=df_ebola,right=df_ebola_date,how='left',left_on='date',right_on='date')

# Marcação da origem da doença
df_ebola['origem'] = np.logical_and(df_ebola['contador_dia']==1, df_ebola['tt_cases'] != 0)
df_ebola['origem'] = np.where(df_ebola['origem'] == False,0,1)


# tt cases negativos
df_ebola[(df_ebola.tt_cases < 0)].count()
# tt deaths negativos
df_ebola[(df_ebola.tt_deaths < 0)].count()

plt.boxplot(df_ebola.iloc[:,4],showfliers=True)
# outiliers tt_deaths
plt.boxplot(df_ebola.iloc[:,5],showfliers=True)




##############################################################################
# H1N1
##############################################################################

df_h1n1 = pd.read_csv(directory+'data/dataset_H1N1.csv',sep=",",encoding='unicode_escape')
df_h1n1['category'] = 'h1n1'
df_h1n1['continent'] = 'null'
df_h1n1.columns=['country','tt_cases','tt_deaths','date','category','continent']
df_h1n1['date'] = pd.to_datetime(df_h1n1['date'])
df_h1n1['date'] = df_h1n1['date'].dt.strftime('%Y-%m-%d')

# Alterar nomes de paises invalidos
df_h1n1["country"] = df_h1n1["country"].replace(['Korea, Republic of'],'South Korea')
df_h1n1["country"] = df_h1n1["country"].replace(['Viet Nam'],'Vietnam')
df_h1n1["country"] = df_h1n1["country"].replace(['Brunei Darussalam'],'Brunei')
df_h1n1["continent"] = df_h1n1["continent"].where(df_h1n1["country"] == "Guatemala").replace('','North America')
#df_h1n1 = df_h1n1["country"].where("Guatemala",df_h1n1['continent']== 'North America',df_h1n1['continent'])
df_h1n1['country_merge'] = df_h1n1['country'].str[:8]
df_h1n1 = df_h1n1[['category','date','country','country_merge','continent','tt_cases','tt_deaths']]

# merge para classificar continent
df_h1n1 = pd.merge(left=df_h1n1,right=df_country_covid,how='left',left_on='country_merge',right_on='country')
df_h1n1 = df_h1n1.rename(columns={"country_x":"country","continent_y":"continent"})
df_h1n1 = df_h1n1[["category","date","country","continent","tt_cases","tt_deaths"]]
df_h1n1_index_to_drop = df_h1n1[df_h1n1['country']== "Grand Total"].index
df_h1n1.drop(df_h1n1_index_to_drop , inplace=True)

# Gerar acumulado por dias
df_h1n1_date = df_h1n1['date'].dropna().drop_duplicates()
df_h1n1_date = pd.DataFrame(df_h1n1_date)
df_h1n1_date['contador_dia'] = 1
df_h1n1_date['contador_dia'] = df_h1n1_date['contador_dia'].cumsum()
df_h1n1 = pd.merge(left=df_h1n1,right=df_h1n1_date,how='left',left_on='date',right_on='date')

# Marcação da origem da doença
df_h1n1['origem'] = np.logical_and(df_h1n1['contador_dia']==1, df_h1n1['tt_cases'] != 0)
df_h1n1['origem'] = np.where(df_h1n1['origem'] == False,0,1)


# tt cases negativos
df_h1n1[(df_h1n1.tt_cases < 0)].count()
# tt deaths negativos
df_h1n1[(df_h1n1.tt_deaths < 0)].count()

df_h1n1_outliers = df_h1n1.dropna()

plt.boxplot(df_h1n1_outliers.iloc[:,4],showfliers=True)
# outiliers tt_deaths
plt.boxplot(df_h1n1_outliers.iloc[:,5],showfliers=True)



##############################################################################
# SARS
##############################################################################

df_sars = pd.read_csv(directory+'data/dataset_sars.csv',sep=",")
df_sars['category'] = 'sars'
df_sars['continent'] = 'null'
df_sars.columns=['date','country','tt_cases','tt_deaths','tt_recovery','category','continent']

# Alterar nomes de paises invalidos
df_sars["country"] = df_sars["country"].replace(['Hong Kong SAR, China'],'China')
df_sars["country"] = df_sars["country"].replace(['Taiwan, China'],'China')
df_sars["country"] = df_sars["country"].replace(['Macao SAR, China'],'China')
df_sars["country"] = df_sars["country"].replace(['Viet Nam'],'Vietnam')
df_sars["country"] = df_sars["country"].replace(['Russian Federation'],'Russia')
df_sars["country"] = df_sars["country"].replace(['Republic of Ireland'],'Ireland')
df_sars["country"] = df_sars["country"].replace(['Republic of Korea'],'South Korea')

df_sars['country_merge'] = df_sars['country'].str[:8]
df_sars = df_sars[['category','date','country','country_merge','continent','tt_cases','tt_deaths']]

# merge para classificar continent
df_sars = pd.merge(how='left',left=df_sars,right=df_country_covid,left_on='country_merge',right_on='country')
df_sars = df_sars.rename(columns={"country_x":"country","continent_y":"continent"})
df_sars = df_sars[["category","date","country","continent","tt_cases","tt_deaths"]]

# Gerar acumulado por dias
df_sars_date = df_sars['date'].dropna().drop_duplicates()
df_sars_date = pd.DataFrame(df_sars_date)
df_sars_date['contador_dia'] = 1
df_sars_date['contador_dia'] = df_sars_date['contador_dia'].cumsum()
df_sars = pd.merge(left=df_sars,right=df_sars_date,how='left',left_on='date',right_on='date')

# Marcação da origem da doença
df_sars['origem'] = np.logical_and(df_sars['contador_dia']==1, df_sars['tt_cases'] != 0)
df_sars['origem'] = np.where(df_sars['origem'] == False,0,1)

# tt cases negativos
df_sars[(df_sars.tt_cases < 0)].count()
# tt deaths negativos
df_sars[(df_sars.tt_deaths < 0)].count()

df_sars_outliers = df_sars.dropna()

plt.boxplot(df_sars.iloc[:,4],showfliers=True)
# outiliers tt_deaths
plt.boxplot(df_sars.iloc[:,5],showfliers=True)


df_final = pd.concat([df_covid,df_ebola,df_h1n1,df_sars])

#df_final.to_excel(directory+'teste_new.xlsx')

print("Periodo de covid19 entre: " + str(df_covid['date'].min())[:10]+" e "+str(df_covid['date'].max())[:10])
print("Periodo de ebola entre: " + str(df_ebola['date'].min())+" e "+str(df_ebola['date'].max()))
print("Periodo de h1n1 entre: " + str(df_h1n1['date'].min())+" e "+str(df_h1n1['date'].max()))
print("Periodo de sars entre: " + str(df_sars['date'].min())+" e "+str(df_sars['date'].max()))


# Carregar no big query

pk_json_input = directory+"credentials/tcc-pucminas-bot-analytics-c354df613281.json"

project_input = "tcc-pucminas-bot-analytics"

auth = service_account.Credentials.from_service_account_file(pk_json_input)

pandas_gbq.to_gbq(
    df_final,'botanalytics_log.tb_pandemic_data',project_id=project_input,if_exists='replace',
)

database_connection = sqlalchemy.create_engine('postgresql://airflow:airflow@dags_postgres_1/postgres')

#database_connection

#df_final_teste = df_final.tail(1)
df_final.to_sql(con=database_connection,name='tb_pandemics',if_exists='replace')

#query_select = """
#SELECT * FROM tb_pandemics;
#"""

#df_select_teste = pd.read_sql(query_select, con=database_connection)

#df_select_teste 
