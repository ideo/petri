import streamlit as st
import pandas as pd


# load baseline excel data
df = pd.read_excel("D FORD ACCESS (1).xlsx")


# fix headers - weird split across 2 rows
df.rename(
    columns={'Person': 'Person Type', 'Access': 'Access Date', },
    inplace=True,
)


# get rid of junk
df.drop(columns=['Category Used'], inplace=True)  # empty column
df.dropna(inplace=True)  # gets rid of empty rows & that weird split if it's there in future


# convert to string to date
df['Access Date'] = pd.to_datetime(df['Access Date'], format='%d/%m/%Y')
df['Access Date'] = df['Access Date'].dt.date


# anonymize
# if we want to make this more sophisticated... look at hashlib
df['anon_id'] = df['CDSID'].astype('category').cat.codes
df.drop(columns=['Last Name', 'First Name', 'CDSID'], inplace=True)


# we only care if person's card was used during a given day
df.drop(columns=['Person Type', 'Reader Description', 'Transaction Type'], inplace=True)
df.drop_duplicates(inplace=True, ignore_index=True)


# App Output
st.title("Baseline Door Data!")  # add a title
st.write(df.head())


# st.code(df.dtypes)
if __name__ == "__main__":
    print("Hello, World!")
