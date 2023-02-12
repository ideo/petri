import streamlit as st
import pandas as pd
import altair as alt
import datetime
import calendar
from dateutil.relativedelta import relativedelta
import numpy as np


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


def unique_swipes_per_day(df, combined=False):
    if combined:
        return df.groupby(['Access Date', 'Source']).size().rename('Swipe Count').reset_index(level=0)
    else:
        return df.groupby('Access Date').size().rename('Swipe Count').reset_index(level=0)


def unique_swipes_line_chart(df, comparison_df=None):
    st.markdown("""
                ### Unique swipes sensed (Door Agnostic) 
                *Something about this is expected / surprising*
                """)
    # timeseries - unique swipes per day
    lines = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("Access Date:T", title="Access Date"),
            y="Swipe Count",
        )
    )

    if comparison_df is not None:
        comp_lines = (
            alt.Chart(comparison_df)
            .mark_line()
            .encode(
                x=alt.X("Access Date:T", title="Access Date"),
                y="Swipe Count",
            )
        )
        rule = alt.Chart(phases).mark_rule(
            color="black",
            strokeWidth=3
        ).encode(
            x='end:T'
        ).transform_filter(alt.datum.phase == "Pre-Experiment")

        text = alt.Chart(phases).mark_text(
            align='left',
            baseline='middle',
            dx=7,
            dy=-135,
            size=11
        ).encode(
            x='start:T',
            x2='end:T',
            text='phase',
            color=alt.value('#000000')
        )
        st.altair_chart(lines + comp_lines + rule + text, theme=None, use_container_width=True)
    else:
        st.altair_chart(lines, theme=None, use_container_width=True)


def bars_and_rolling_average(df):
    st.markdown("""
                ### Getting to what's "typical" 
                *Something about this is expected / surprising*
                """)

    line = alt.Chart(df).mark_line(color='red').transform_window(
        # The field to average
        rolling_mean='mean(Swipe Count)',
        # The number of values before and after the current value to include.
        frame=[-5, 0]
    ).encode(
        x='Access Date:T',
        # y='rolling_mean:Q'
        y=alt.Y('rolling_mean:Q', title='Rolling Mean of Swipe Count'),
    ).interactive()

    bar = alt.Chart(df).mark_bar().encode(
        x='Access Date:T',
        y='Swipe Count:Q'
    )

    st.altair_chart(bar + line, theme=None, use_container_width=True)


def boxplot_by_day(df):
    st.markdown("""
                ### Midweek is the busiest 
                *Something about this is expected / surprising*
                """)

    # SPLIT BY DAY OF WEEK
    df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Day Of Week'] = df['Day Of Week'].dt.day_name()

    # BOXPLOTS - group by day of week
    chart = alt.Chart(df).mark_boxplot().encode(
        x=alt.X('Day Of Week', sort=day_names),
        y='Swipe Count',
        color=alt.Color('Day Of Week', sort=day_names),
    ).interactive()

    st.altair_chart(chart, theme=None, use_container_width=True)


def timeseries_by_day(df):
    st.markdown("""
                ### Thursday & Tuesday consistently most crowded 
                *Something about this is expected / surprising*
                """)

    # TIMESERIES - group by day of week
    chart = alt.Chart(df).mark_line().encode(
        x='Access Date',
        y='Swipe Count',
        color=alt.Color('Day Of Week', sort=['Monday'])
    ).interactive()

    st.altair_chart(chart, theme=None, use_container_width=True)


def extract_variables(df, file_type='Baseline'):
    min_date_value = df['Access Date'].min()
    max_date_value = df['Access Date'].max()
    person_types = df['Person Type'].unique()

    st.title(f"{file_type} Door Data!")  # add a title
    st.subheader(f"{min_date_value:%a, %d %b %Y} - {max_date_value:%a, %d %b %Y}")

    return min_date_value, max_date_value, person_types


def baseline_tab(df):
    # constant variables based on data
    min_date_value, max_date_value, person_types = extract_variables(df)

    st.markdown("""
                 TKTK put some copy here to explain site
                 TKTK put some copy here to explain site
                 TKTK put some copy here to explain site
                 TKTK put some copy here to explain site
                 TKTK put some copy here to explain site
                 TKTK put some copy here to explain site

               *This is emphasized*. **Anonymized!!!**
     """)

    st.markdown("""
                 ### Disclaimer: door swipe data undercounts. 
                 *On busier days, even more likely to undercount as tailgating is more likely*
                 """)

    st.markdown("""
                    ## Understanding Baseline Behaviour   
                    ##### What are the utilization patterns pre-experiment?

                    Description - data cleaned. removed some data intentionally .
                    """)

    # Filter options - person type, dates, weekend
    df, _ = filter_options(df, person_types)

    # aggregate unique swipes by day
    swipe_cnts_df = unique_swipes_per_day(df)

    # GRAPHS

    # OVERVIEW
    unique_swipes_line_chart(swipe_cnts_df)
    bars_and_rolling_average(swipe_cnts_df)

    # SPLIT BY DAY OF WEEK
    boxplot_by_day(swipe_cnts_df)
    timeseries_by_day(swipe_cnts_df)


def upload_data(baseline_headers):
    uploaded_file = st.file_uploader("Choose a comparison file (csv or xlsx)")
    if uploaded_file is not None:
        extension = uploaded_file.name.split('.')[-1]
        # Can be used wherever a "file-like" object is accepted:
        if extension == 'csv':
            # st.code("reading cvs")
            dataframe = pd.read_csv(uploaded_file)
        elif extension == 'xlsx':
            dataframe = pd.read_excel(uploaded_file)
        else:
            st.code("Incompatiable file. Try .csv or .xlsx")
            return

        df, baseline_headers = clean_and_validate_df(dataframe, baseline_headers)
        return df


def comparison_tab(baseline_df, debug=False):
    comparison_df = upload_data(baseline_headers)

    if debug:
        # add 2 months to baseline data
        comparison_df = baseline_df.copy()
        comparison_df['Access Date'] = baseline_df['Access Date'] + relativedelta(months=+2)
        comparison_df['Day Of Week'] = pd.to_datetime(comparison_df['Access Date'], format='%Y-%m-%d')
        comparison_df['Day Of Week'] = comparison_df['Day Of Week'].dt.day_name()

    if comparison_df is not None:
        min_date_value, max_date_value, person_types = extract_variables(comparison_df, file_type='Comparison')

    # COMBINE DATA
    baseline_df['Source'] = 'Baseline'
    comparison_df['Source'] = 'Comparison'
    combined_df = pd.concat([baseline_df, df], ignore_index=True)
    min_date_value, max_date_value, person_types = extract_variables(combined_df, file_type='Combined')

    # Filter options - person type, dates, weekend
    baseline_df, comparison_df = filter_options(baseline_df, person_types, tab="comparison", compare_df=comparison_df)

    # aggregate unique swipes by day
    baseline_swipe_cnts_df = unique_swipes_per_day(baseline_df)
    comparison_swipe_cnts_df = unique_swipes_per_day(comparison_df)
    if debug:
        # Randomly add or subtract up to 5 swipes per day
        np.random.seed(42)
        comparison_swipe_cnts_df['Swipe Count'] = comparison_swipe_cnts_df['Swipe Count'] + np.random.randint(-5, 5)

    # GRAPHS

    # OVERVIEW
    unique_swipes_line_chart(baseline_swipe_cnts_df, comparison_df=comparison_swipe_cnts_df)
    # bars_and_rolling_average(swipe_cnts_df)
    #
    # # SPLIT BY DAY OF WEEK
    # boxplot_by_day(swipe_cnts_df)
    # timeseries_by_day(swipe_cnts_df)


    # HUNCHES
    # more people will come on wednesdays

    # do more people on other days too?
    # do people come less ?
    # combo of both?


def swiper_patterns(df):
    # constant variables based on data
    min_date_value, max_date_value, person_types = extract_variables(df)
    # Filter options - person type, dates, weekend
    df,_ = filter_options(df, person_types, tab='swiper')

    # how many days a week is the same card used?
    st.code(df.head())
    # st.code(df.groupby('anon_id').size())
    # .size().rename('Swipe Count').reset_index(level=0)

    # some people come 1 day a week, some 5 - what's the distribution?
    # each week (or month or range), look at hist of how often same card is used in time period

    # per card, look at avg times in studio per week (across baseline)
    # buttons to remove contractors!!
    # remove weekend & holiday

    # note - missing tailgaters
    # note - missing events (brings in more people) & trips (to Detroit or elsewhere)
    # note - WFH is still work :)


if __name__ == "__main__":
    df, baseline_headers = load_baseline()

    tab1, tab2, tab3 = st.tabs(["Baseline", "Patterns by Swiper", "Comparison"])
    # App Output
    with tab1:
        baseline_tab(df)

    with tab2:
        swiper_patterns(df)

    with tab3:
        comparison_tab(df, debug=True)
