import streamlit as st
import pandas as pd
import datetime
import calendar

date_format = '%d/%m/%Y'
day_names = list(calendar.day_name)

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

def remove_weekend(baseline_df, tab, compare_df=None):
    remove = st.radio("Remove weekends?", (True, False), 0, key=f'wknd_{tab}', horizontal=True)
    if remove:
        baseline_df = remove_weekend_data(baseline_df)
        compare_df = remove_weekend_data(compare_df)
    return baseline_df, compare_df


def remove_holiday_data(df):
    if df is not None:
        start_date, end_date = datetime.date(2022, 12, 17), datetime.date(2023, 1, 6)
        # locate indices
        holiday_idx = df[(df['Access Date'] >= start_date) & (df['Access Date'] <= end_date)].index
        # drop by indices
        if holiday_idx is not None:
            df = df.drop(holiday_idx)
    return df


def remove_holiday(baseline_df, tab, compare_df=None):
    remove = st.radio("Remove Holidays? (Sat, 17 Dec 2022 - Sun, 06 Jan 2023) ",
                      (True, False), 0, key=f'hols_{tab}', horizontal=True)
    if remove:
        baseline_df = remove_holiday_data(baseline_df)
        compare_df = remove_holiday_data(compare_df)
    return baseline_df, compare_df


def include_person_type_data(df, options, person_types):
    if df is not None:
        for type in person_types:
            if type not in options:
                person_type_idx = df[df['Person Type'] == type].index
                df = df.drop(person_type_idx)
    return df

def include_persons(baseline_df, person_types, tab, compare_df=None):
    options = st.multiselect(
        'Who to include?',
        person_types,
        person_types,
        key=f'persons_{tab}'
    )
    baseline_df = include_person_type_data(baseline_df, options, person_types)
    compare_df = include_person_type_data(compare_df, options, person_types)
    return baseline_df, compare_df


def filter_options(df, person_types, tab='baseline', compare_df=None):
    sc1, sc2, sc3 = st.columns(3)

    # Remove Weekends button
    with sc1:
        df, compare_df = remove_weekend(df, tab, compare_df)

    # Remove Holidays
    with sc2:
        df, compare_df = remove_holiday(df, tab, compare_df)

    # include all person types by default
    with sc3:
        df, compare_df = include_persons(df, person_types, tab, compare_df)

    return df, compare_df

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


def compatability_check(df, baseline_headers=None):
    # check if comparable to baseline columns
    if baseline_headers is not None:
        comparison_headers = sorted(list(df.columns.values))
        if comparison_headers != baseline_headers:
            st.code('Columns do not match baseline file.')
            min_required_headers = [x for x in baseline_headers if x not in ["Last Name", "First Name"]]
            st.code(f'Required Columns: {min_required_headers}')
            st.code(f"Uploaded File Columns: {comparison_headers}")
            return df, baseline_headers, False
    else:
        # extract here b/c some columns are dropped during anonymize
        baseline_headers = sorted(list(df.columns.values))
    return df, baseline_headers, True


def clean_and_validate_df(df, baseline_headers=None):
    df = fix_headers(df)
    df = remove_junk(df)
    df, baseline_headers, is_compatible = compatability_check(df, baseline_headers)
    if is_compatible:
        print('compatible')
        print(df.head())
        df = fix_dates(df)
        df = anonymize(df)
        df = count_one_swipe_per_day(df)
    else:
        df = None
    return df, baseline_headers


def load_baseline(f="data/D FORD ACCESS (1).xlsx"):
    df = pd.read_excel(f)
    df, baseline_headers = clean_and_validate_df(df)
    return df, baseline_headers

