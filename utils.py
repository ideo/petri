import streamlit as st
import pandas as pd
import datetime
import calendar

date_format = '%d/%m/%Y'
day_names = list(calendar.day_name)
experiment_start_date = datetime.date(2023, 2, 8)

phases = pd.DataFrame([
    {
        "start": "2022-11-01",
        "end": "2023-02-07",
        "phase": "Pre-Experiment"
    },
    {
        "start": "2023-02-08",
        # "end": "2015-12-31",
        "phase": "Post-Experiment"
    }
])

def fix_headers(df):
    # fix headers - weird split across 2 rows
    return df.rename(
        columns={'Person': 'Person Type', 'Access': 'Access Date', },
    )


def remove_weekend_data(df):
    if df is not None:
        # locate indices
        sat_idx = df[df['Day Of Week'] == 'Saturday'].index
        sun_idx = df[df['Day Of Week'] == 'Sunday'].index
        # drop by indices
        df = df.drop(sat_idx)
        df = df.drop(sun_idx)
    return df

def remove_weekend(df, tab):
    remove = st.radio("Remove weekends?", (True, False), 0, key=f'wknd_{tab}', horizontal=True)
    if remove:
        df = remove_weekend_data(df)
    return df

def filter_by_experiment_date(df):
    if df is not None:
        # locate indices
        post_experiment_idx = df[(df['Access Date'] >= experiment_start_date)].index
        # drop by indices
        if post_experiment_idx is not None:
            df = df.drop(post_experiment_idx)
    return df


def remove_holiday_data(df):
    if df is not None:
        start_date, end_date = datetime.date(2022, 12, 17), datetime.date(2023, 1, 6)
        # locate indices
        holiday_idx = df[(df['Access Date'] >= start_date) & (df['Access Date'] <= end_date)].index
        # drop by indices
        if holiday_idx is not None:
            df = df.drop(holiday_idx)
    return df


def remove_holiday(df, tab, baseline=False):
    remove = st.radio("Remove Holidays? (Sat, 17 Dec 2022 - Sun, 06 Jan 2023) ",
                      (True, False), 0, key=f'hols_{tab}', horizontal=True)
    if baseline:
        df = filter_by_experiment_date(df)
    if remove:
        df = remove_holiday_data(df)
    return df


def include_person_type_data(df, options, person_types):
    if df is not None:
        for type in person_types:
            if type not in options:
                person_type_idx = df[df['Person Type'] == type].index
                df = df.drop(person_type_idx)
    return df

def include_persons(df, person_types, tab):
    options = st.multiselect(
        'Who to include?',
        person_types,
        person_types,
        key=f'persons_{tab}'
    )
    df = include_person_type_data(df, options, person_types)
    return df

def filter_options(df, person_types, tab='baseline', baseline=False):
    sc1, sc2, sc3 = st.columns(3)

    # Remove Weekends button
    with sc1:
        df = remove_weekend(df, tab)

    # Remove Holidays & Other Date Filters
    with sc2:
        df = remove_holiday(df, tab, baseline)

    # include all person types by default
    with sc3:
        df = include_persons(df, person_types, tab)

    return df

def remove_junk(df):
    # gets rid of empty rows & that weird split if it's there in future
    if 'Category Used' in df.columns:  # since empty, this might be removed in future
        df.drop(columns=['Category Used'], inplace=True)  # empty column
    return df.dropna()


def fix_dates(df):
    # convert to string to date
    df['Access Date'] = pd.to_datetime(df['Access Date'], format=date_format)
    df['Day Of Week'] = df['Access Date'].dt.day_name()
    df['Access Date'] = df['Access Date'].dt.date
    return df


def anonymize(df):
    # if we want to make this more sophisticated... look at hashlib
    df['anon_id'] = df['CDSID'].astype('category').cat.codes
    return df.drop(columns=['Last Name', 'First Name', 'CDSID'])


def count_one_swipe_per_day(df):
    # we only care if person's card was used during a given day
    df.drop(columns=['Reader Description', 'Transaction Type'], inplace=True)
    return df.drop_duplicates(ignore_index=True)


def clean_df(df):
    df = fix_headers(df)
    df = remove_junk(df)
    df = fix_dates(df)
    df = anonymize(df)
    df = count_one_swipe_per_day(df)
    return df

def upload_data_file():
    is_unlocked = False
    baseline_df = None
    uploaded_file = st.file_uploader("Upload data file (csv or xlsx)")

    if uploaded_file is not None:
        extension = uploaded_file.name.split('.')[-1]
        # Can be used wherever a "file-like" object is accepted:
        if extension == 'csv':
            baseline_df = pd.read_csv(uploaded_file)
        elif extension == 'xlsx':
            baseline_df = pd.read_excel(uploaded_file)
        else:
            st.code("Incompatiable file. Try .csv or .xlsx")
            return baseline_df, is_unlocked

        # Required Headers - Extra will be handled and removed; Less will be rejected
        min_required_headers = ['Access Date', 'CDSID', 'Person Type',]
        baseline_df = fix_headers(baseline_df)

        if all(item in baseline_df.columns.to_list() for item in min_required_headers):
            is_unlocked = True
            baseline_df = clean_df(baseline_df)
        else:
            st.code('TRY AGAIN!')

    return baseline_df, is_unlocked

