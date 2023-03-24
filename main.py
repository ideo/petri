import altair as alt
import pandas as pd
from dateutil.relativedelta import relativedelta
import numpy as np
from utils import *
from PIL import Image

def print_chart_df(df):
    with st.expander("See chart data"):
        st.dataframe(df)

def print_pretty_df(df):
    # st.table(df.style.format('{:7,.2f}'))
    st.table(df)

def print_summary_stats(df, dataframe=False):
    if dataframe:
        st.dataframe(df.describe().style.format('{:7,.2f}'))
    else:
        st.table(df.describe().style.format('{:7,.2f}'))

def unique_swipes_per_day(df, combined=False):
    if combined:
        return df.groupby(['Access Date', 'Source']).size().rename('Swipe Count').reset_index(level=0)
    else:
        return df.groupby('Access Date').size().rename('Swipe Count').reset_index(level=0)


def unique_swipes_line_chart(df, compare_option="Experiment", tab="Baseline", pct=False, show_data=False):
    # timeseries - unique swipes per day

    if pct:
        df['Pct Lab Population'] = df['Swipe Count'] / lab_population_n
        st.markdown(f"""
                        ### Percent of Lab Employee Population Sensed 
                        *Only looking as Employees of London Lab / Excludes Contractors & Temp 
                        (total employee n={lab_population_n})*
                        """)
        summaryX = alt.X("Pct Lab Population:Q", title="Pct Lab Employee Population", axis=alt.Axis(format='.0%'))
        linesY = alt.Y("Pct Lab Population:Q", title="Pct Lab Employee Population", axis=alt.Axis(format='.0%'))
    else:
        st.markdown("""
                    ### Unique swipes sensed (Door Agnostic Counts) 
                    *Something about this is expected / surprising*
                    """)
        summaryX = alt.X("Swipe Count:Q", title="Swipe Count")
        linesY = "Swipe Count"

    if compare_option == "Experiment":
        compare = "Source"
    else:
        compare = "Quarter"

    if tab == "Comparison":
        df['Source'] = 'Baseline'
        df.loc[df['Access Date'] >= experiment_start_date, 'Source'] = 'Post-Experiment'
        summary = (
            alt.Chart(df)
            .mark_boxplot()
            .encode(
                x=summaryX,
                # y="Quarter",
                # color="Quarter",
                y=compare,
                color=compare,
            ).properties(
                height=300
            )
        )
    else:
        summary = (
            alt.Chart(df)
            .mark_boxplot()
            .encode(
                x=summaryX,
            ).properties(
                height=150
            )
        )
    lines = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("Access Date:T", title="Access Date", axis=alt.Axis(labelAngle=45)),
            y=linesY,
        )
    ).interactive()

    if tab == "Comparison":
        st.altair_chart(summary, theme=None, use_container_width=True)
        print_summary_stats(df.groupby(compare))
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(summary, theme=None, use_container_width=True)
        with col2:
            print_summary_stats(df)

    if tab == "Comparison":
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
        # st.altair_chart(lines + comp_lines + rule + text, theme=None, use_container_width=True)
        st.altair_chart(lines + rule + text, theme=None, use_container_width=True)
    else:

        st.altair_chart(lines, theme=None, use_container_width=True)

    if show_data:
        print_chart_df(df)


def counts_over_time_bar_chart(df):

    bar = alt.Chart(df).mark_bar().encode(
        x=alt.X("Access Date:T", title="Access Date", axis=alt.Axis(labelAngle=45)),
        y='Swipe Count:Q'
    )

    st.altair_chart(bar, theme=None, use_container_width=True)
    print_chart_df(df)

def boxplot_by_day(df, compare_option="Experiment", tab="Baseline"):
    if tab == 'Baseline':
        st.markdown("""
                    ### Midweek is the busiest 
                    *Something about this is expected / surprising*
                    """)

    # SPLIT BY DAY OF WEEK
    df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Day Of Week'] = df['Day Of Week'].dt.day_name()

    if tab == 'Comparison':
        if compare_option == 'Experiment':
            compare = 'Source'
        elif compare_option == 'Quarter':
            compare = 'Quarter'

        df['Source'] = 'Baseline'
        df.loc[df['Access Date'] >= experiment_start_date, 'Source'] = 'Post-Experiment'

        chart = alt.Chart(df).mark_boxplot().encode(
            # alt.Column('Day Of Week'),
            x=alt.X(compare, title=None, axis=alt.Axis(labels=False, ticks=False), scale=alt.Scale(padding=1)),
            y='Swipe Count',
            color=compare,
        ).facet(
            column=alt.Column('Day Of Week:O', sort=day_names)
        ).interactive()
        st.altair_chart(chart, theme=None)

    else:
        # BOXPLOTS - group by day of week
        chart = alt.Chart(df).mark_boxplot().encode(
            x=alt.X('Day Of Week', sort=day_names, axis=alt.Axis(labelAngle=0)),
            y='Swipe Count',
            color=alt.Color('Day Of Week', sort=day_names),
        ).interactive()
        st.altair_chart(chart, theme=None, use_container_width=True)
        # ensure describe outputs correct day order
        filtered_days = [day for day in day_names if day in df['Day Of Week'].unique()]
        category_day = pd.api.types.CategoricalDtype(categories=filtered_days, ordered=True)
        df['Day Of Week'] = df['Day Of Week'].astype(category_day)


def timeseries_by_day(df, compare_option="Experiment", tab="Baseline"):
    # if tab == "Baseline":
        # st.markdown("""
        #             ### Thursday & Tuesday consistently most crowded
        #             *Something about this is expected / surprising*
        #             """)
    if compare_option == 'Experiment':
        compare = "Source"
    else:
        compare = "Quarter"
    # TIMESERIES - group by day of week
    chart = alt.Chart(df).mark_line().encode(
        x='Access Date',
        y='Swipe Count',
        color=alt.Color('Day Of Week', sort=['Monday'])
    ).interactive()

    if tab == 'Comparison':

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
        st.altair_chart(chart + rule + text, theme=None, use_container_width=True)
        print_summary_stats(df.groupby(['Day Of Week', compare])['Swipe Count'], dataframe=True)
        print_chart_df(df)
    else:
        st.altair_chart(chart, theme=None, use_container_width=True)
        print_summary_stats(df.groupby('Day Of Week')['Swipe Count'])
        print_chart_df(df)

def extract_variables(df, file_type='Baseline'):
    min_date_value = df['Access Date'].min()
    max_date_value = df['Access Date'].max()
    person_types = df['Person Type'].unique()

    return min_date_value, max_date_value, person_types


def baseline_tab(raw_df):
    # constant variables based on data
    min_date_value, max_date_value, person_types = extract_variables(raw_df)

    st.title(f"Baseline Door Data!")  # add a title
    st.subheader(f"Baseline Dates: {min_date_value:%a, %d %b %Y} - {experiment_start_date + relativedelta(days=-1):%a, %d %b %Y}")

    st.markdown(f"""
                 This Streamlit app has been purpose built for the London lab, Project Petri “All In Wednesdays” experiment. 
                 It is solely accessible by uploading the London lab entry data. 
               
               **Baseline Population of London Lab: {lab_population_n} people**
     """)

    st.markdown("""
                 ### Disclaimer: door swipe data undercounts. 
                 Daily entries into the lab have only been counted once per day and solely from the external lab doors. 
                 We assume there may be some undercounting as tailgating through the Lab doors often occurs. 
                 It may be that not everyone present at the lab on a given day is counted for.
                 
                 *On busier days, even more likely to undercount as tailgating is more likely*
                 """)

    st.markdown("""
                    ## Understanding Baseline Behaviour   
                    ##### What are the utilization patterns pre-experiment?

                    Description - data cleaned. removed some data intentionally .
                    """)

    # Employee only data for some graphs
    employee_df = include_employees_only_data(raw_df)
    employee_only_swipe_cnts_df = unique_swipes_per_day(employee_df)

    # aggregate unique swipes by day
    swipe_cnts_df = unique_swipes_per_day(raw_df)

    # GRAPHS

    # OVERVIEW
    unique_swipes_line_chart(swipe_cnts_df)
    counts_over_time_bar_chart(swipe_cnts_df)
    unique_swipes_line_chart(employee_only_swipe_cnts_df, pct=True, show_data=True)

    # SPLIT BY DAY OF WEEK
    boxplot_by_day(swipe_cnts_df)
    timeseries_by_day(swipe_cnts_df)

    swiper_patterns(raw_df)

def add_quarters(df):
    df['Quarter'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Quarter'] = df['Quarter'].dt.to_period('Q').dt.strftime('%YQ%q')
    return df

def comparison_tab(raw_df, compare_option="Experiment", debug=False):
    # DATES FOR HEADER
    # min_baseline_date, max_baseline_date , person_types = extract_variables(df)
    if debug:
        st.header('DEBUG MODE')

    min_date_value, max_date_value, person_types = extract_variables(raw_df)

    st.title(f"Post Experiment Comparison")  # add a title
    st.subheader(
        f"Dates: {experiment_start_date:%a, %d %b %Y} - {max_date_value:%a, %d %b %Y}")
    st.markdown(f"""
                     This view allows for comparison of Door Data patterns post experiment start date with Baseline

                   **Baseline Population of London Lab: {lab_population_n} people**
         """)
    # Filter options - person type, dates, weekend
    # df = filter_options(df, person_types, tab="comparison")

    # aggregate unique swipes by day
    swipe_cnts_df = unique_swipes_per_day(raw_df)
    swipe_cnts_df = add_quarters(swipe_cnts_df)

    # Employee only data for some graphs
    employee_df = include_employees_only_data(raw_df)
    employee_only_swipe_cnts_df = unique_swipes_per_day(employee_df)
    employee_only_swipe_cnts_df = add_quarters(employee_only_swipe_cnts_df)

    # #
    if debug:
        # Randomly add or subtract up to 5 swipes per day
        np.random.seed(42)
        swipe_cnts_df['Swipe Count'] = swipe_cnts_df['Swipe Count'] + np.random.randint(-5, 5)
        employee_only_swipe_cnts_df['Swipe Count'] = employee_only_swipe_cnts_df['Swipe Count'] + np.random.randint(-5, 5)

    df['Source'] = 'Baseline'
    df.loc[df['Access Date'] >= experiment_start_date, 'Source'] = 'Post-Experiment'


    # GRAPHS
    # OVERVIEW
    unique_swipes_line_chart(swipe_cnts_df, compare_option, tab="Comparison", show_data=True)
    unique_swipes_line_chart(employee_only_swipe_cnts_df, compare_option,pct=True, tab="Comparison", show_data=True)

    # # SPLIT BY DAY OF WEEK
    boxplot_by_day(swipe_cnts_df, compare_option, tab="Comparison")
    timeseries_by_day(swipe_cnts_df, compare_option, tab="Comparison")

    raw_df = add_quarters(raw_df)
    # swiper_patterns(raw_df, compare_option, tab="Comparison")

    # HUNCHES
    # more people will come on wednesdays

    # do more people on other days too?
    # do people come less ?
    # combo of both?


def swiper_patterns(df, compare_option="Experiment", tab="Baseline"):

    # SPLIT BY DAY OF WEEK
    df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Day Of Week'] = df['Day Of Week'].dt.day_name()
    df['Year-Week'] = pd.to_datetime(df['Access Date']).dt.strftime('%Y-%U')

    df['Source'] = 'Baseline'
    df.loc[df['Access Date'] >= experiment_start_date, 'Source'] = 'Post-Experiment'

    if compare_option == "Experiment":
        compare = "Source"
    else:
        compare = "Quarter"

    # how many days a week is the same card used?

    # some people come 1 day a week, some 5 - what's the distribution?
    # each week (or month or range), look at hist of how often same card is used in time period

    if tab == 'Baseline':
        st.markdown("""
                ### Most People Come Once a Week to Lab
                *Something about this is expected / surprising*
                """)

        df2 = df.groupby(['anon_id', 'Year-Week']).size().to_frame(name='Repeat Visits Per Week').reset_index().copy()
        chart = alt.Chart(df2).mark_bar().encode(
            y=alt.Y('count():Q', title="Percent", axis=alt.Axis(labelAngle=0, format='.0%'), stack="normalize"),
            color = 'Repeat Visits Per Week:O'
        ).properties(
                # height=500
        ).interactive()
    else:
        st.dataframe(df)
        df2 = df.groupby(['anon_id', 'Year-Week']).size().to_frame(name='Repeat Visits Per Week').reset_index().copy()
        chart = not not alt.Chart(df2).mark_bar().encode(
            # x="Quarter",
            # x=compare,
            x=compare,
            y=alt.Y('count():Q', title="Percent", axis=alt.Axis(labelAngle=0, format='.0%'), stack="normalize"),
            color='Repeat Visits Per Week:O'
        ).properties(
            # height=500
        ).interactive()


    if tab == 'Baseline':
        col1, col2 = st.columns(2)

        print_df = df2.groupby(['Repeat Visits Per Week']).size().to_frame(
            name='Total Times Card Swiped X Times a Week')
        total_visits = print_df['Total Times Card Swiped X Times a Week'].sum()
        print_df['Percent'] = print_df['Total Times Card Swiped X Times a Week'] / total_visits
        print_df.index.name = 'Repeat Visits Per Week'
        print_df.reset_index(inplace=True)

        with col1:
            print_pretty_df(print_df)

        with col2:
            st.altair_chart(chart, theme=None, use_container_width=True)
    else:
        st.altair_chart(chart, theme=None, use_container_width=True)
    # chart = alt.Chart(df2).mark_boxplot().encode(
    #     x=alt.X('Repeat Visits:O', axis=alt.Axis(labelAngle=0)),
    #     y=alt.Y("datum['Year-Week'].mean()"),
    # ).interactive()
    # # chart = alt.Chart(df2).mark_boxplot().encode(
    # #     x=alt.X('Day Of Week', sort=day_names, axis=alt.Axis(labelAngle=0)),
    # #     y='Swipe Count',
    # #     color=alt.Color('Day Of Week', sort=day_names),
    # # ).interactive()
    # st.altair_chart(chart, theme=None, use_container_width=True)
    # #
    # #
    # # # per card, look at avg times in studio per week (across baseline)
    #
    chart2 = alt.Chart(df2).mark_line().encode(
        x=alt.X('Year-Week:N', title="Year-Week",axis=alt.Axis(labelAngle=45)),
        y=alt.Y("count()", title="Repeat Visits Per Week", axis=alt.Axis(labelAngle=0)),
        color=alt.Color('Repeat Visits Per Week:N')
    ).interactive()

    st.altair_chart(chart2, theme=None, use_container_width=True)
    # print_summary_stats(df2.groupby('Repeat Visits Per Week'))
    print_chart_df(df2)
    # # note - missing tailgaters
    # # note - missing events (brings in more people) & trips (to Detroit or elsewhere)
    # # note - WFH is still work :)


def generate_fake_data(df):
    # add 2 months to baseline data
    faux_df = df.copy()
    faux_df['Access Date'] = df['Access Date'] + relativedelta(months=+4)
    faux_df['Day Of Week'] = pd.to_datetime(faux_df['Access Date'], format='%Y-%m-%d')
    faux_df['Day Of Week'] = faux_df['Day Of Week'].dt.day_name()
    faux_df = remove_weekend_data(faux_df)
    df = pd.concat([df, faux_df], ignore_index=True)
    return df

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def sidebar(raw_df):
    # Filter options - person type, dates, weekend
    _, _, person_types = extract_variables(raw_df)
    st.subheader("""Filter Options""")
    df = filter_options(raw_df, person_types)
    st.write("""
        ---
        """)
    st.subheader("""Comparison Tab Option - Only Affects Some Graphs""")
    compare_option = st.radio("Compare By", ("Experiment", "Quarter"), 0, horizontal=True)
    # DEBUG
    debug = st.radio("Debug Comparison Tab?", (True, False), 1, horizontal=True)
    # DOWNLOAD CLEAN CVS option
    st.write("""
    ---
    """)
    st.subheader("""Further Analysis""")
    st.write('To run further analysis, download cvs. Data is anonymized and door agnostic')
    csv = convert_df(raw_df)
    st.download_button(
        label="Download clean data as CSV",
        data=csv,
        file_name='anonymous_door_data.csv',
        mime='text/csv'
    )
    return df, debug, compare_option


if __name__ == "__main__":
    is_unlocked = False
    raw_df, is_unlocked = upload_data_file()


    if is_unlocked:
        with st.sidebar:
            df, debug, compare_option = sidebar(raw_df)

        tab1, tab2 = st.tabs(["Baseline", "Comparison"])
        # App Output

        with tab1:
            baseline_tab(df)

        with tab2:
            if debug:
                faux_df = generate_fake_data(df)
                comparison_tab(faux_df, compare_option, debug=True)
            else:
                comparison_tab(df, compare_option)
    else:

        st.code('Welcome! Upload the Correct Data to Unlock')
        image = Image.open('red_door.jpeg')
        st.image(image, caption='Red Door - Upload the Correct Data to Unlock')
