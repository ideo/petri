import streamlit as st
import pandas as pd
import altair as alt
import datetime


date_format = '%d/%m/%Y'

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
    df['Access Date'] = pd.to_datetime(df['Access Date'], format=date_format)
    df['Day Of Week'] = df['Access Date'].dt.day_name()
    df['Access Date'] = df['Access Date'].dt.date
    # st.write(df.dtypes)
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
# st.write(df.head())


if __name__ == "__main__":
    print("Hello, World!")

    df = load_baseline()
    min_date_value = df['Access Date'].min()
    max_date_value = df['Access Date'].max()

    # App Output
    st.title("Baseline Door Data!")  # add a title

    # Remove Weekends button
    remove_weekend = st.radio("Remove weekends?", (True, False), 0, horizontal=True)
    if remove_weekend:
        # locate indices
        sat_idx = df[df['Day Of Week'] == 'Saturday'].index
        sun_idx = df[df['Day Of Week'] == 'Sunday'].index
        # drop by indices
        df = df.drop(sat_idx)
        df = df.drop(sun_idx)


    # Remove Holidays
    remove_holidays = st.radio("Remove Holidays? (Sat, 17 Dec 2022 - Sun, 06 Jan 2023) ",
                               (True, False), 0, horizontal=True)
    if remove_holidays:
        start_date, end_date = datetime.date(2022, 12, 17), datetime.date(2023, 1, 6)
        # start_date, end_date = st.date_input('Time Period to Remove',
        #                                      value=[datetime.date(2022, 12, 17),
        #                                             datetime.date(2023, 1, 6)],
        #                                      min_value=min_date_value,
        #                                      max_value=max_date_value
        #                                      )


        # locate indices
        holiday_idx = df[(df['Access Date'] >= start_date) & (df['Access Date'] <= end_date)].index
        # drop by indices
        df = df.drop(holiday_idx)


    # timeseries - unique swipes per day
    swipe_cnts_df = df.groupby('Access Date').size().rename('Swipe Count').reset_index(level=0)
    st.line_chart(data=swipe_cnts_df, x='Access Date', y='Swipe Count')


    swipe_cnts_df['Day Of Week'] = pd.to_datetime(swipe_cnts_df['Access Date'], format='%Y-%m-%d')
    swipe_cnts_df['Day Of Week'] = swipe_cnts_df['Day Of Week'].dt.day_name()

    chart = alt.Chart(swipe_cnts_df).mark_line().encode(
        x='Access Date',
        y='Swipe Count',
        color=alt.Color('Day Of Week', sort=['Monday'])
    ).interactive()

    st.altair_chart(chart, theme=None, use_container_width=True)