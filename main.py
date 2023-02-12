import streamlit as st
import pandas as pd
import altair as alt
import datetime
import calendar

date_format = '%d/%m/%Y'
day_names = list(calendar.day_name)

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
    # df.drop(columns=['Person Type', 'Reader Description', 'Transaction Type'], inplace=True)
    df.drop(columns=['Reader Description', 'Transaction Type'], inplace=True)
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


def remove_weekend(df):
    remove = st.radio("Remove weekends?", (True, False), 0, horizontal=True)
    if remove:
        # locate indices
        sat_idx = df[df['Day Of Week'] == 'Saturday'].index
        sun_idx = df[df['Day Of Week'] == 'Sunday'].index
        # drop by indices
        df = df.drop(sat_idx)
        df = df.drop(sun_idx)
    return df

def remove_holiday(df):
    remove = st.radio("Remove Holidays? (Sat, 17 Dec 2022 - Sun, 06 Jan 2023) ",
                           (True, False), 0, horizontal=True)
    if remove:
        start_date, end_date = datetime.date(2022, 12, 17), datetime.date(2023, 1, 6)
        # locate indices
        holiday_idx = df[(df['Access Date'] >= start_date) & (df['Access Date'] <= end_date)].index
        # drop by indices
        df = df.drop(holiday_idx)
    return df


def include_persons(df, person_types):
    options = st.multiselect(
        'Who to include?',
        person_types,
        person_types)

    for type in person_types:
        if type not in options:
            person_type_idx = df[df['Person Type'] == type].index
            df = df.drop(person_type_idx)
    return df


def unique_swipes_per_day(df):
    return df.groupby('Access Date').size().rename('Swipe Count').reset_index(level=0)


def unique_swipes_line_chart(df):
    st.markdown("""
                ### Unique swipes sensed (Door Agnostic) 
                *Something about this is expected / surprising*
                """)
    # timeseries - unique swipes per day
    st.line_chart(data=df, x='Access Date', y='Swipe Count')


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
        color=alt.Color('Day Of Week', sort=['Monday']),
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


def baseline_tab(df):
    min_date_value = df['Access Date'].min()
    max_date_value = df['Access Date'].max()
    person_types = df['Person Type'].unique()

    st.title("Baseline Door Data!")  # add a title
    st.subheader(f"{min_date_value:%a, %d %b %Y} - {max_date_value:%a, %d %b %Y}")

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

    # Radio buttons
    sc1, sc2, sc3 = st.columns(3)

    # Remove Weekends button
    with sc1:
        df = remove_weekend(df)

    # Remove Holidays
    with sc2:
        df = remove_holiday(df)

    # include all person types by default
    with sc3:
        df = include_persons(df, person_types)

    # aggregate unique swipes by day
    swipe_cnts_df = unique_swipes_per_day(df)

    # GRAPHS

    # OVERVIEW
    unique_swipes_line_chart(swipe_cnts_df)
    bars_and_rolling_average(swipe_cnts_df)

    # SPLIT BY DAY OF WEEK
    boxplot_by_day(swipe_cnts_df)
    timeseries_by_day(swipe_cnts_df)


if __name__ == "__main__":

    df = load_baseline()

    tab1, tab2, tab3 = st.tabs(["Baseline", "Patterns by Swiper", "Comparison"])
    # App Output
    with tab1:
        baseline_tab(df)

