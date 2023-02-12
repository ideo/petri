import streamlit as st
import pandas as pd


def fix_headers(df):
    # fix headers - weird split across 2 rows
    return df.rename(
        columns={'Person': 'Person Type', 'Access': 'Access Date', },
    )


def remove_junk(df):
    # gets rid of empty rows & that weird split if it's there in future
    df.drop(columns=['Category Used'], inplace=True)  # empty column
    return df.dropna()


def fix_dates(df):
    # convert to string to date
    df['Access Date'] = pd.to_datetime(df['Access Date'], format='%d/%m/%Y')
    df['Access Date'] = df['Access Date'].dt.date
    return df


def anonymize(df):
    # if we want to make this more sophisticated... look at hashlib
    df['anon_id'] = df['CDSID'].astype('category').cat.codes
    return df.drop(columns=['Last Name', 'First Name', 'CDSID'])


def count_one_swipe_per_day(df):
    # we only care if person's card was used during a given day
    df.drop(columns=['Person Type', 'Reader Description', 'Transaction Type'], inplace=True)
    return df.drop_duplicates(ignore_index=True)


def clean_df(df):
    df = fix_headers(df)
    df = remove_junk(df)
    df = fix_dates(df)
    df = anonymize(df)
    df = count_one_swipe_per_day(df)
    return df


def load_baseline(f="D FORD ACCESS (1).xlsx"):
    df = pd.read_excel(f)
    df = clean_df(df)
    return df


# st.code(df.dtypes)
if __name__ == "__main__":
    print("Hello, World!")

    df = load_baseline()

    # App Output
    st.title("Baseline Door Data!")  # add a title
    st.write(df.head())