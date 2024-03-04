import pandas as pd
import streamlit as st
import json
import ast
import numpy as np
import unicodedata
import openpyxl
import datetime

# Function to load the DataFrame
def load_data():
    df = pd.read_csv('decretos_y_leyes_temas_filtered.csv')
    cols = df.select_dtypes(include=[object]).columns
    df[cols] = df[cols].apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
    df['Temas'] = df['Temas'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df['Date'] = pd.to_datetime(df['Date']).dt.date  # Ensure 'Date' is in date format
    return df

df = load_data()

# Function to load the JSON data
@st.cache_data
def load_json():
    if False: print('')
    with open('tesauro-json.json', encoding='utf-8') as json_file:
        return json.load(json_file)

data = load_json()

# Streamlit UI setup
st.title('Explorador de Leyes y Decretos Argentina')

# Function to search the JSON data for a given search term
def search_categories(data, search_term):
    def recurse(data, current_path=[]):
        if isinstance(data, dict):
            for key, value in data.items():
                if search_term.lower() == key.lower():
                    return " > ".join(current_path + [key])
                found_path = recurse(value, current_path + [key])
                if found_path:
                    return found_path
        return None

    if search_term.lower() == 'todos':
        return 'Todos'

    return recurse(data)


# Streamlit UI for search bar and displaying possible matches
choice = st.sidebar.selectbox('Seleccionar Tema', ['Todos'] + df['Temas'].explode().value_counts().index.to_list())


if choice and choice != 'Todos':
    path = search_categories(data, choice)
    if path:
        st.sidebar.write("Categoría Seleccionada: " + path)
    else:
        st.sidebar.write("No se encontraron coincidencias. Intente nuevamente.")

def filter_df(df, choice):

    # Check if selected_themes is empty, return original df if it is
    if choice == 'Todos':
        return df

    # Filter the DataFrame to include rows where the 'Temas' list intersects with selected_themes
    else:   
        choice = choice.lower()
        return df[df['Temas'].apply(lambda x: choice in [j.lower() for j in x])]

# Filter the DataFrame based on the selected tema
filtered_df = filter_df(df, choice)
filtered_df = filtered_df.sort_values(by='Date', ascending=False)

col1, col2, col3 = st.columns(3)

with col1:
    # Set a checkbox that is checked by default       
    if st.checkbox('Mostrar Version Limpia'):
        filtered_df = filtered_df[(filtered_df['Eliminado'] != 1)]

with col2:
    if st.checkbox('Mostrar solo Decretos Kirchneristas'):
        filtered_df = filtered_df[filtered_df['K'] == 1]

with col3:
    if st.checkbox('Mostrar solo Decretos Reglamentarios'):
        filtered_df = filtered_df[filtered_df['Temas'].apply(lambda x: 'decreto reglamentario' in [j.lower() for j in x])]

    
filtered_df = filtered_df[['Name', 'Date', 'Tipo', 'Numero', 'URL']]

# Display the DataFrame as wide as possible
st.dataframe(filtered_df.style.set_properties(**{'text-align': 'left'}).set_table_styles([dict(selector='th', props=[('text-align', 'left')])]))


st.write('Total: ', len(filtered_df))

# Add a button to download the excel file
@st.cache_data
def convert_df(filtered_df):
   return filtered_df.to_csv(index=False).encode('utf-8')

csv = convert_df(filtered_df)

st.download_button(
   "Descargar",
   csv,
   "file.csv",
   "text/csv",
   key='download-csv'
)


