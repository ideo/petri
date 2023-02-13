import altair as alt
from dateutil.relativedelta import relativedelta
import numpy as np
from utils import *


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
            color="orange",
            strokeWidth=3
        ).encode(
            x='start:T'
        ).transform_filter(alt.datum.phase == "Post-Experiment")

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


def boxplot_by_day(df, compare_df=None):
    st.markdown("""
                ### Midweek is the busiest 
                *Something about this is expected / surprising*
                """)

    # SPLIT BY DAY OF WEEK
    df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Day Of Week'] = df['Day Of Week'].dt.day_name()
    if compare_df is not None:
        compare_df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
        compare_df['Day Of Week'] = compare_df['Day Of Week'].dt.day_name()

        compare_df['Source'] = 'Comparison'
        df['Source'] = 'Baseline'
        combined_df = pd.concat([compare_df, df])

        chart = alt.Chart(combined_df).mark_boxplot().encode(
            # alt.Column('Day Of Week'),
            x=alt.X('Source', title=None, axis=alt.Axis(labels=False, ticks=False), scale=alt.Scale(padding=1)),
            y='Swipe Count',
            # color="Source:N",
            column=alt.Column('Day Of Week', sort=day_names, header=alt.Header(orient='bottom')),
            color=alt.Color('Day Of Week', sort=day_names),
        ).properties(
            width=120
        ).configure_facet(
            spacing=0
        ).configure_view(
            stroke=None
        ).interactive()
        # st.altair_chart(chart, theme=None, use_container_width=True)
        st.altair_chart(chart, theme=None)

    else:
        # BOXPLOTS - group by day of week
        chart = alt.Chart(df).mark_boxplot().encode(
            x=alt.X('Day Of Week', sort=day_names, axis=alt.Axis(labelAngle=0)),
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


def extract_variables(df, file_type='Baseline', header=True):
    min_date_value = df['Access Date'].min()
    max_date_value = df['Access Date'].max()
    person_types = df['Person Type'].unique()

    if header:
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


def remove_overlap_dates(df, filter_date):
    remove_idx = df[(df['Access Date'] <= filter_date)].index
    # drop by indices
    if remove_idx is not None:
        df = df.drop(remove_idx)
    return df


def comparison_tab(baseline_df, debug=False):
    comparison_df = upload_data(baseline_headers)
    min_baseline_date, max_baseline_date , _ = extract_variables(baseline_df, header=False)

    if debug:
        # add 2 months to baseline data
        comparison_df = baseline_df.copy()
        comparison_df['Access Date'] = baseline_df['Access Date'] + relativedelta(months=+2)
        comparison_df['Day Of Week'] = pd.to_datetime(comparison_df['Access Date'], format='%Y-%m-%d')
        comparison_df['Day Of Week'] = comparison_df['Day Of Week'].dt.day_name()

    if comparison_df is not None:
        # remove overlap dates
        comparison_df = remove_overlap_dates(comparison_df, max_baseline_date)
        _, _, _ = extract_variables(comparison_df, file_type='Comparison')

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
    boxplot_by_day(baseline_swipe_cnts_df,compare_df=comparison_swipe_cnts_df)
    timeseries_by_day(comparison_swipe_cnts_df)


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
