import altair as alt
from dateutil.relativedelta import relativedelta
import numpy as np
from utils import *
from PIL import Image

def unique_swipes_per_day(df, combined=False):
    if combined:
        return df.groupby(['Access Date', 'Source']).size().rename('Swipe Count').reset_index(level=0)
    else:
        return df.groupby('Access Date').size().rename('Swipe Count').reset_index(level=0)


def unique_swipes_line_chart(df, tab="Baseline", pct=False):
    # timeseries - unique swipes per day
    if pct:
        st.markdown(f"""
                        ### Percent of Lab Employee Population Sensed 
                        *Only looking as Employees of London Lab (total employee n={lab_population_n})*
                        """)
        df['Pct Lab Population'] = df['Swipe Count']/lab_population_n
        lines = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("Access Date:T", title="Access Date"),
                y=alt.Y("Pct Lab Population:Q", title="Pct Lab Employee Population", axis=alt.Axis(format='%')),
            )
        ).interactive()

    else:
        st.markdown("""
                    ### Unique swipes sensed (Door Agnostic) 
                    *Something about this is expected / surprising*
                    """)
        lines = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("Access Date:T", title="Access Date"),
                y="Swipe Count",
            )
        ).interactive()
    #
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


def boxplot_by_day(df, tab="Baseline"):
    if tab == 'Baseline':
        st.markdown("""
                    ### Midweek is the busiest 
                    *Something about this is expected / surprising*
                    """)

    # SPLIT BY DAY OF WEEK
    df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Day Of Week'] = df['Day Of Week'].dt.day_name()

    if tab == 'Comparison':
        df['Source'] = 'Baseline'
        df.loc[df['Access Date'] >= experiment_start_date, 'Source'] = 'Comparison'

        chart = alt.Chart(df).mark_boxplot().encode(
            # alt.Column('Day Of Week'),
            x=alt.X('Source', title=None, axis=alt.Axis(labels=False, ticks=False), scale=alt.Scale(padding=1)),
            y='Swipe Count',
            color="Source:N",
            column=alt.Column('Day Of Week', sort=day_names, header=alt.Header(orient='bottom')),
            # color=alt.Color('Day Of Week', sort=day_names),
        ).properties(
            width=100
            # width=120
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


def timeseries_by_day(df, tab="Baseline"):
    if tab == "Baseline":
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

    else:
        st.altair_chart(chart, theme=None, use_container_width=True)


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
    employee_df = include_employees_only_data(df)
    employee_only_swipe_cnts_df = unique_swipes_per_day(employee_df)

    # aggregate unique swipes by day
    swipe_cnts_df = unique_swipes_per_day(df)

    # GRAPHS

    # OVERVIEW
    unique_swipes_line_chart(swipe_cnts_df)
    unique_swipes_line_chart(employee_only_swipe_cnts_df, pct=True)
    bars_and_rolling_average(swipe_cnts_df)

    # SPLIT BY DAY OF WEEK
    boxplot_by_day(swipe_cnts_df)
    timeseries_by_day(swipe_cnts_df)

    swiper_patterns(df)

def comparison_tab(df, debug=False):
    # DATES FOR HEADER
    # min_baseline_date, max_baseline_date , person_types = extract_variables(df)
    if debug:
        st.header('DEBUG MODE')


    # Filter options - person type, dates, weekend
    # df = filter_options(df, person_types, tab="comparison")

    # aggregate unique swipes by day
    swipe_cnts_df = unique_swipes_per_day(df)

    # #
    if debug:
        # Randomly add or subtract up to 5 swipes per day
        np.random.seed(42)
        swipe_cnts_df['Swipe Count'] = swipe_cnts_df['Swipe Count'] + np.random.randint(-5, 5)


    # GRAPHS
    # OVERVIEW
    unique_swipes_line_chart(swipe_cnts_df, tab="Comparison")

    # # SPLIT BY DAY OF WEEK
    boxplot_by_day(swipe_cnts_df, tab="Comparison")
    timeseries_by_day(swipe_cnts_df, tab="Comparison")


    # HUNCHES
    # more people will come on wednesdays

    # do more people on other days too?
    # do people come less ?
    # combo of both?


def swiper_patterns(df):

    # SPLIT BY DAY OF WEEK
    df['Day Of Week'] = pd.to_datetime(df['Access Date'], format='%Y-%m-%d')
    df['Day Of Week'] = df['Day Of Week'].dt.day_name()
    df['Year-Week'] = pd.to_datetime(df['Access Date']).dt.strftime('%Y-%U')

    # how many days a week is the same card used?

    # some people come 1 day a week, some 5 - what's the distribution?
    # each week (or month or range), look at hist of how often same card is used in time period

    st.markdown("""
                ### Most People Come Once a Week to Lab 
                *Something about this is expected / surprising*
                """)
    df2 = df.groupby(['anon_id', 'Year-Week']).size().to_frame(name='Repeat Visits').reset_index()
    chart = alt.Chart(df2).mark_bar().encode(
        x=alt.X('Repeat Visits:O', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('count()', title="Count",axis=alt.Axis(labelAngle=0)),
    ).interactive()
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


    # per card, look at avg times in studio per week (across baseline)
    st.markdown("""
                ### Special Events Bring People in More Often  
                *Something about this is expected / surprising*
                """)
    chart2 = alt.Chart(df2).mark_line().encode(
        x=alt.X('Year-Week:N', title="Year-Week",axis=alt.Axis(labelAngle=0)),
        y=alt.Y("count()", title="Repeat Visits in a Week", axis=alt.Axis(labelAngle=0)),
        color=alt.Color('Repeat Visits:N')
    ).interactive()

    st.altair_chart(chart2, theme=None, use_container_width=True)

    # note - missing tailgaters
    # note - missing events (brings in more people) & trips (to Detroit or elsewhere)
    # note - WFH is still work :)


def generate_fake_data(df):
    # add 2 months to baseline data
    faux_df = df.copy()
    faux_df['Access Date'] = df['Access Date'] + relativedelta(months=+2)
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
    df = filter_options(raw_df, person_types)
    # DEBUG
    debug = st.radio("Debug Comparison Tab?", (True, False), 0, horizontal=True)
    # DOWNLOAD CLEAN CVS option
    st.write("""
    ---
    To run further analysis, download cvs. Data is anonymized and door agnostic
    """)
    csv = convert_df(raw_df)
    st.download_button(
        label="Download clean data as CSV",
        data=csv,
        file_name='anonymous_door_data.csv',
        mime='text/csv'
    )
    return df, debug


if __name__ == "__main__":
    is_unlocked = False
    raw_df, is_unlocked = upload_data_file()


    if is_unlocked:
        with st.sidebar:
            df, debug = sidebar(raw_df)

        tab1, tab2 = st.tabs(["Baseline", "Comparison"])
        # App Output

        with tab1:
            baseline_tab(df)

        with tab2:
            if debug:
                faux_df = generate_fake_data(df)
                comparison_tab(faux_df, debug=True)
            else:
                comparison_tab(df)
    else:

        st.code('Welcome! Upload the Correct Data to Unlock')
        image = Image.open('red_door.jpeg')
        st.image(image, caption='Red Door - Upload the Correct Data to Unlock')
