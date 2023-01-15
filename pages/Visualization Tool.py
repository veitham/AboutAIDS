import streamlit as st
import pandas as pd
import numpy as np
import re
from textwrap import wrap
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import plotly.express as px
import json

# Import data   
df = pd.read_csv("data/hiv.csv",sep=";")
df["Estimated Value"] = df["Value"].apply(lambda x: x.replace(',','').replace('<','').replace('>','') if type(x)==str else x).astype(float)
df["Upper Value"] = df["Upper"].apply(lambda x: x.replace(',','').replace('<','').replace('>','') if type(x)==str else x).astype(float)
df["Lower Value"] = df["Lower"].apply(lambda x: x.replace(',','').replace('<','').replace('>','') if type(x)==str else x).astype(float)

descriptions = json.load(open('data/indicators.json', 'r')) 
number_ind = ['Estimated number of annual AIDS-related deaths','Estimated number of annual new HIV infections','Estimated number of people living with HIV']

# Functions
@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')

def get_steps(age_groups_by_ind): #returns the steps for the age slider
    temp =[]
    for ag in age_groups_by_ind:
        temp.extend(re.findall(r'\d+', ag))
    temp = list(set(temp))
    steps  = []
    for i in temp:
        if int(i)%5 == 0:
            steps.append(int(i))
        else:
            steps.append(int(i)+1)
    steps = list(set(steps))
    steps.sort()
    return steps

# Title 
st.title("Visualization Tool")  

# Sidebar (Infos)
st.sidebar.title("AIDS and the youth") 
st.sidebar.write("To use the tool, simply select the indicator you want to visualize, and select the parameters. Then, select how you want to visualize the data.\n\n")

################################## INTRO ##################################

# Indicator selection
st.write("Select the indicator you would like to explore:")
indicators = df["Indicator"].unique()
indicator = st.selectbox('Indicator',indicators)
# Description and title
st.subheader(indicator)
st.write(descriptions[indicator]) 

# First data
fcol1,fcol2,fcol3 = st.columns(3)   

country_df = df[(df['Type']!='Region') & (df['Sex']=='Both') & (df['Year']==max(df['Year'].unique())) & (df['Indicator']==indicator)]
global_df = df[(df['Country/Region']=='Global') & (df['Sex']=='Both') & (df['Year']==max(df['Year'].unique())) & (df['Indicator']==indicator)]
gen_df = df[ (df['Sex']!='Both') & (df['Year']==max(df['Year'].unique())) & (df['Indicator']==indicator) & (df['Country/Region']=='Global')]

country_max = country_df.groupby('Country/Region')['Estimated Value'].mean().idxmax()
val_max = country_df.groupby('Country/Region')['Estimated Value'].mean().max()
mean = float(global_df.groupby('Indicator')['Estimated Value'].mean())
gender_rep = gen_df.groupby('Sex')['Estimated Value'].mean().reset_index()

mean = round(mean) if indicator in number_ind else round(mean,2)
val_max = round(val_max) if indicator in number_ind else round(val_max,2)

with fcol1: 
    st.markdown('<br><br><br>', unsafe_allow_html=True)
    st.metric("Today in the world",mean)
with fcol2:
    st.markdown('<br><br><br>', unsafe_allow_html=True)
    st.metric("Most affected country",country_max ,val_max,delta_color="off")
with fcol3:
    pie = px.pie(gender_rep, values='Estimated Value', names='Sex', color_discrete_sequence=['#F5B787','#87C5F5'],height=250)
    st.plotly_chart(pie,use_container_width=True)

st.markdown('<hr>', unsafe_allow_html=True)

################################## PARAMETERS ##################################
st.header("Parameters")

col0,col1= st.columns(2)

# Gender selection
with col0:
    st.markdown('<br><br>', unsafe_allow_html=True)
    st.caption('Gender')
    male = st.checkbox('Male')
    female = st.checkbox('Female')

both = not(male or female)
both2 = (male and female)
gender = ["Both"]
if male:
    gender = ["Male"]
if female:
    gender = ["Female"]
if both:
    gender = ["Both"]
if both2:
    gender = ["Male","Female"]

# Age selection
with col1:
    age_choice = st.radio(
        "Age selection",
        ["Any", "Age group"],
        horizontal=True
    )
    st.caption("'Any' will select the mean value of all age groups. It won't give precisely accurate values, but will help to vizualise.")

    st.session_state.disabled = False if age_choice == "Age group" else True

    age_groups_by_ind = (df.loc[df['Indicator'] == indicator])["Age"].unique()
    steps = get_steps(age_groups_by_ind)
    start_age, end_age = st.select_slider(
        'Age group(s):',
        options=steps,
        value=(min(steps),max(steps)),
        disabled=st.session_state.disabled
    )
    if not st.session_state.disabled:
        st.caption("Available age groups : " + ", ".join(age_groups_by_ind))

age = "Age "+str(start_age)+"-"+str(end_age-1)

# Year selection
years = (df.loc[df['Indicator'] == indicator])["Year"].unique()
start_year, end_year = st.select_slider(
    'Year(s):',
    options=years,
    value=(min(years),max(years)))

# Country selection
countries = list((df.loc[df['Indicator'] == indicator])["Country/Region"].unique())
countries.remove('Global')
country = st.multiselect(
    'Countries (this parameter does not affect the map)',
    countries)
if len(country)==0:
    country = ['Global']

any_age = st.session_state.disabled
# New Dataframes definition (user choice)
user_mask = (df['Indicator'] == indicator) & (df['Year'] >= start_year) & (df['Year'] <= end_year)
user_mask = user_mask & (df['Age'] == age) if not any_age else user_mask #if "Any" selected, select the mean/sum of all age groups (for a year or country). this is not really correct in terms of numbers, since it risks duplicating values, but it helps for the vizualisation.
chart_mask = user_mask & (df['Country/Region'].isin(country)) & (df['Sex'].isin(gender))
map_mask = user_mask & (df['Type']!='Region') 
map_mask = (map_mask & (df['Sex']=='Both') ) if both2 else ( map_mask & (df['Sex'].isin(gender)) ) # if male and female both selected, workaround the gender config and only select 'Both' for the map, else do as usual

df_chart = df[chart_mask]
df_map = df[map_mask]


st.write(str(len(df_chart)) + " rows selected")

############################ VIZUALISATION ############################

# Tabs
chart, map, table = st.tabs(["📈 Chart", "🗺️ Map", "📊 Table"])

# Dynamic titles definition (chosen gender and countries)
g = "" if both or both2 else gender[0]
c = "" if (len(country)==1 and country[0]=='Global') or (len(country)==0) else "in "+ ", ".join(country)
a = "between the ages "+"-".join(re.findall(r'\d+', age)) if not any_age else "between the ages 0-19"
chart_title = "Evolution of the "+indicator+" in the "+g+" population "+a+" over the years "+str(start_year)+" to "+str(end_year) +" "+ c
chart_title = "<br>".join(wrap(chart_title, 90))
map_title = "Map of the "+indicator+" in the "+g+" population "+a+" over the years "+str(start_year)+" to "+str(end_year)
table_title = "Data concerning the "+indicator+" in the "+g+" population "+a+" over the years "+str(start_year)+" to "+str(end_year) +" "+ c


# CHART vizualisation
with chart:
    st.subheader("Chart :")
    show_ul = st.checkbox('Show Upper/lower values',value=True)
    fig = go.Figure()
    fig.update_layout(title=chart_title)

    for cou in country:
        for gen in gender:
            temp = df_chart[ (df_chart['Sex']==gen) & (df_chart['Country/Region']==cou) ]
            temp = temp.groupby('Year')[['Estimated Value','Lower Value','Upper Value']].mean().reset_index() if any_age else temp
            disp_cou = '('+cou+')' if cou != 'Global' else ''
            disp_gen = '('+gen[0]+')' if gen != 'Both' else ''
            fig.add_trace(go.Scatter(x=temp['Year'], y=temp["Estimated Value"], mode='lines',name="Estimated Value"+disp_gen+'<br>'+disp_cou))
            if show_ul:
                fig.add_trace(go.Scatter(x=temp['Year'], y=temp["Upper Value"], mode='lines',name="Upper Value"+disp_gen+'<br>'+disp_cou))
                fig.add_trace(go.Scatter(x=temp['Year'], y=temp["Lower Value"], mode='lines',name="Lower Value"+disp_gen+'<br>'+disp_cou))
    st.plotly_chart(fig)


# MAP vizualisation
with map:
    st.subheader("Map :")
    st.write(map_title)
    m = folium.Map(location=[0, 0], zoom_start=1)

    df_map = df_map.groupby(['ISO3','Year'])[['Estimated Value','Lower Value','Upper Value']].mean().reset_index()

    # Summarizes the data when a year range is selected
    if indicator in ["Estimated incidence rate (new HIV infection per 1,000 uninfected population)", "Estimated mother-to-child transmission rate (%)","Estimated number of people living with HIV"]:
        df_map = (df_map.groupby("ISO3")["Estimated Value"].mean()).reset_index()
    else:
        df_map = (df_map.groupby("ISO3")["Estimated Value"].sum()).reset_index()
        
    cho_map = folium.Choropleth(
        geo_data="data/countries.geojson",
        name="choropleth",
        data=df_map,
        columns=["ISO3", "Estimated Value"],
        key_on="feature.properties.ISO_A3",
        fill_color="Reds",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=indicator
    ).add_to(m)

    df_indexed = df_map.set_index('ISO3')
    for feature in cho_map.geojson.data['features']:
        iso3 = feature['properties']["ISO_A3"]
        feature['properties']['nb'] =  'Estimate:' + str( np.sum(df_indexed.loc[iso3, 'Estimated Value'])) if iso3 in list(df_indexed.index) else 'missing data'
    
    cho_map.geojson.add_child(
        folium.features.GeoJsonTooltip(['ADMIN', 'nb'], labels=False)
    )
    folium_static(m)

# TABLE Viz
with table:
    st.subheader("Table :")
    st.write(table_title)
    st.write(df_chart)

    csv = convert_df(df_chart)
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name='selection.csv',
        mime='text/csv',
    )



#TODO
# change colors?
# explore data