import streamlit as st
import pandas as pd
from PIL import Image

df = pd.read_csv("data/hiv.csv",sep=";")

st.sidebar.title("About the project")
st.sidebar.write("This is the introduction page of the project. To use the visualisation tool, use the navigation menu above.")

st.title("What about AIDS and the youth ?")
st.write(
    "According to the UNICEF, the HIV/AIDS pandemic is still a major public health issue, especially in the youth: "
    "Of the estimated 650,000 people who died of AIDS-related illnesses in 2021, 17% of them were children under 20 years of age.\n\n"
    "The purpose of this project is to allow, through data visualisation and inspection, a better understanding of the HIV (in particular its most advanced and dangerous stage, AIDS), its evolution in the world and its impact on the youth in particular.\n\n"
    "To do so, we can vizualize the UNICEF HIV/AIDS dataset, which offers different informations about the spread of AIDS in the world's youth specifically.\n\n"
    "The dataset contains "+str(df.shape[0])+" rows and "+str(df.shape[1])+" columns, covering "+str(len(df["Country/Region"].unique()))+" countries, about men and women aged between 0 and 19 years old, from 2000 to 2021.\n\n"
    "The dataset is available on the UNICEF website: https://data.unicef.org/topic/hiv-aids/"
    )

st.subheader("UNICEF Infographic : gender, treatment and regional disparities")
image = Image.open('data/unicef_ig.gif')
st.image(image, caption='UNICEF infographic from the Global Annual Results Report 2021')

st.caption("Project by : Matthieu Andreani")

