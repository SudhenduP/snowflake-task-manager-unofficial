# Tested on Python 3.9

# import statement START
import time
from datetime import datetime
import tzlocal
import pandas as pd
import plotly.graph_objects as go
import snowflake.connector
import streamlit as st
from plotly.subplots import make_subplots
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import os

# import statement END


# setting page config- START
st.set_page_config(layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #1489a6;'>❄❄ SN❄WFLAKE TASK MANAGER ❄❄</h1>",
    unsafe_allow_html=True)

# page configurtion end


# Css https://docs.streamlit.io/knowledge-base/using-streamlit/hide-row-indices-displaying-dataframe
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)

# setting page config- END


# Variable declaration START
file_dir = os.path.dirname(os.path.dirname(__file__))
task_list_file = (file_dir + '/data/task.csv')
task_hist_file = (file_dir + '/data/task_hist.csv')
current_tz =  "'"+ tzlocal.get_localzone_name() + "'"
print(tzlocal.get_localzone_name())
print(file_dir)
print(task_list_file)
print(task_hist_file)


def current_dt():
    now = datetime.now()
    datetime_string = now.strftime("%d-%m-%Y %H:%M:%S")
    return datetime_string


# Variable declaration END


# Creating Snowflake Connection Object START
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

conn = init_connection()

@st.experimental_memo(ttl=600)
@st.experimental_singleton
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


# Creating Snowflake Connection Object END

# Loading Data from Snowflake START
@st.experimental_memo(ttl=600)
@st.experimental_singleton
def load_data_task_list():
    # load_dt = current_dt()
    ls_all = run_query(
        'SHOW TASKS IN ACCOUNT;')
    df_task = pd.DataFrame(ls_all,
                           columns=['CREATED_ON', 'NAME', 'ID', 'DATABASE_NAME', 'SCHEMA_NAME', 'OWNER', 'COMMENT',
                                    'WAREHOUSE', 'SCHEDULE', 'PREDECESSORS', 'STATE', 'DEFINITION', 'CONDITION',
                                    'ALLOW_OVERLAPPING_EXECUTION', 'ERROR_INTEGRATION', 'LAST_COMMITTED_ON',
                                    'LAST_SUSPENDED_ON'])

    df_task['CREATED_ON'] = df_task['CREATED_ON'].dt.strftime('%Y-%m-%d %H:%M:%S')

    df_task.to_csv(task_list_file, index=False)
    final_df_task_list = pd.read_csv(task_list_file)
    loadtime_list = current_dt()
    print('Task List Data is loaded from Snowflake at: ', loadtime_list)
    return final_df_task_list, loadtime_list

# In the below query, we are usign the TASK_HISTORY() function.
# This function returns task activity within the last 7 days
# or the next scheduled execution within the next 8 days.
# Ideally, if you would like to get more information,
# you can use the base table: SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY.

@st.experimental_singleton
def load_data_task_hist():
    current_dt()
    st.write("SELECT NAME, DATABASE_NAME,  SCHEMA_NAME, date_trunc( 'second', CONVERT_TIMEZONE(" + current_tz +
        ", SCHEDULED_TIME) ) as SCHEDULED_TIME, STATE, date_trunc( 'second', CONVERT_TIMEZONE(" + current_tz +
        ", QUERY_START_TIME) ) as START_TIME, date_trunc( 'second', CONVERT_TIMEZONE(" + current_tz +
        ", COMPLETED_TIME) ) as END_TIME, TIMESTAMPDIFF('millisecond', "
        "QUERY_START_TIME, COMPLETED_TIME) as DURATION, ERROR_CODE, ERROR_MESSAGE, QUERY_ID, "
        "NEXT_SCHEDULED_TIME, SCHEDULED_FROM FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.TASK_HISTORY()) ORDER BY SCHEDULED_TIME DESC")
    ls_all = run_query(
        "SELECT NAME, DATABASE_NAME,  SCHEMA_NAME, date_trunc( 'second', CONVERT_TIMEZONE(" + current_tz +
        ", SCHEDULED_TIME) ) as SCHEDULED_TIME, STATE, date_trunc( 'second', CONVERT_TIMEZONE(" + current_tz +
        ", QUERY_START_TIME) ) as START_TIME, date_trunc( 'second', CONVERT_TIMEZONE(" + current_tz +
        ", COMPLETED_TIME) ) as END_TIME, TIMESTAMPDIFF('millisecond', "
        "QUERY_START_TIME, COMPLETED_TIME) as DURATION, ERROR_CODE, ERROR_MESSAGE, QUERY_ID, "
        "NEXT_SCHEDULED_TIME, SCHEDULED_FROM FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.TASK_HISTORY()) ORDER BY SCHEDULED_TIME DESC;")

    df_hist = pd.DataFrame(ls_all, columns=[ 'NAME', 'DATABASE_NAME', 'SCHEMA_NAME', 'SCHEDULED_TIME',
                                             'STATE', 'START_TIME', 'END_TIME',
                                            'DURATION',  'ERROR_CODE', 'ERROR_MESSAGE', 'QUERY_ID',
                                            'NEXT_SCHEDULED_TIME','SCHEDULED_FROM'])

    #df_hist['SCHEDULED_TIME'] = df_hist['SCHEDULED_TIME'].dt.strftime('%m-%d-%y %H:%M:%S')

    df_hist.to_csv(task_hist_file, index=False)
    final_df_task_hist = pd.read_csv(task_hist_file)
    loadtime_hist = current_dt()
    print('Task History Data is loaded from Snowflake at: ', loadtime_hist)
    return final_df_task_hist, loadtime_hist


# Loading Data from Snowflake END


with st.spinner("Please wait while we load the Data from Snowflake..."):
    task_list, load_dt_list = load_data_task_list()
    task_hist, load_dt_hist = load_data_task_hist()
    st.success('Snowflake Data Successful loaded!', icon="✅")

# Creating Snowflake Connection Object END


# TAB definition START
tab1, tab2, tab3, tab4 = st.tabs(["📈 TASK SUMMARY", "📜 TASK LIST", "🗃 TASK HISTORY", "🏃 EXECUTE TASK"])

# TAB1
with tab1:
    fig_count = make_subplots(
        rows=2, cols=2,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}],
        ],
        horizontal_spacing=0, vertical_spacing=0
    )

    total_task_count = len(task_hist)
    total_task_success = len(task_hist[task_hist['STATE'] == 'SUCCEEDED'])
    total_task_error = len(task_hist[task_hist['STATE'] == 'FAILED'])
    total_task_scheduled = len(task_hist[task_hist['STATE'] == 'SCHEDULED'])

    fig_count.add_trace(
        go.Indicator(
            mode="number",
            value=total_task_count,
            title="Total Task",

        ),
        row=1, col=1

    )

    fig_count.add_trace(
        go.Indicator(
            mode="number",
            value=total_task_success,
            title="Success",
            number={'font_color': 'green'},
        ),
        row=1, col=2
    )

    fig_count.add_trace(
        go.Indicator(
            mode="number",
            value=total_task_scheduled,
            title="Task Scheduled",
        ),
        row=2, col=1
    )

    fig_count.add_trace(
        go.Indicator(
            mode="number",
            value=total_task_error,
            title="Error Task",
            number={'font_color': 'red'},
        ),
        row=2, col=2
    )

    fig_count.update_layout(template="plotly_dark", font_family="Arial",
                            margin=dict(l=20, r=20, t=20, b=20), width=800, height=300)
    st.plotly_chart(fig_count, use_container_width=True)
    # Summary plot for counts - END

    # Showcase timeline start
    # timeline = st_timeline(task_actual_list, groups=[], options={}, height="300px")
    # st.subheader("Selected item")
    # st.write(timeline)

    # col1 = st.columns()
    #    with col1:
    st.markdown(
        "<h1 style='text-align: center; color: black;'>UPCOMING TASK",
        unsafe_allow_html=True)

    now = datetime.now()

    dt_string = now.strftime("%Y-%m-%d %H:%M:%S%z")
    # print (dt_string)
    # print('11-02-22 17:00:00' >= dt_string)
    st.table(task_hist.loc[task_hist["NEXT_SCHEDULED_TIME"] >= str(dt_string), ["NAME", "DATABASE_NAME", "SCHEMA_NAME",
                                                                           "NEXT_SCHEDULED_TIME"]].head(10))

# TAB2
with tab2:
    st.markdown(
        "<h1 style='text-align: center; color: black;'>List of Task",
        unsafe_allow_html=True)
    st.markdown(
        "<h5 style='text-align: center; color: #3269a8;'>Below you will find the list of Task. Click on any of the task to see additonal info. Note you can filter, export, slice and dice the below data! ",
        unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align: center; color: black;'>",
        unsafe_allow_html=True)


    def aggrid_task_list_table(df: pd.DataFrame):
        options = GridOptionsBuilder.from_dataframe(
            df, enableRowGroup=True, enableValue=True, enablePivot=True
        )

        options.configure_side_bar()

        options.configure_selection("single")
        selection = AgGrid(
            df,
            enable_enterprise_modules=True,
            gridOptions=options.build(),
            theme="balham",
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True,
        )
        return selection


    col1, col2 = st.columns([3.5, 1])
    with col1:
        selection = aggrid_task_list_table(df=task_list)

    with col2:
        st.write('Below are the details: ')
        if selection:
            st.write("You selected:")
            st.json(selection["selected_rows"])

# TAB3
with tab3:
    # tab1.subheader("History of Task")
    st.markdown(
        "<h1 style='text-align: center; color: black;'>List of task",
        unsafe_allow_html=True)
    st.markdown(
        "<h5 style='text-align: center; color: #3269a8;'>Below you will find the list of Task. To find the run history of any of the taks, please click 'Run History' ",
        unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align: center; color: black;'>",
        unsafe_allow_html=True)

    colms = st.columns((6))

    for col, field_name in zip(colms, ['NAME', 'DATABASE_NAME', 'SCHEMA_NAME', 'STATE', 'SCHEDULED_TIME']):
        col.write(field_name)

    for idx, task_name in enumerate(task_list['NAME']):
        col1, col2, col3, col4, col5, col6 = st.columns((6))
        col1.write(task_list['NAME'][idx])
        col2.write(task_list['DATABASE_NAME'][idx])
        col3.write(task_list['SCHEMA_NAME'][idx])
        col4.write(task_list['STATE'][idx])
        col5.write(task_list['SCHEDULE'][idx])

        placeholder = col6.empty()
        show_more = placeholder.button("Run History", key=task_name)

        # if button pressed
        if show_more:
            placeholder.button("less", key=str(idx) + "_")
            res = task_hist.loc[task_hist['NAME'] == task_name]
            AgGrid(res)

# TAB4
with tab4:
    st.markdown(
        "<h1 style='text-align: center; color: grey;'>Execute Task",
        unsafe_allow_html=True)
    st.markdown(
        "<h5 style='text-align: center; color: #3269a8;'>Please select a task to execute. Please note task might have dependencies, so be sure to execute with caution.",
        unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align: center; color: grey;'>", unsafe_allow_html=True)


    def run_task_list(data):
        st.markdown(f"<div id='linkto_{'Search'}'></div>", unsafe_allow_html=True)
        execute_task_select = st.selectbox(
            'Which task you want to run?',
            data['NAME'].unique())

        st.error("Do you want to run this task?")



        database_name = data[data['NAME'] == execute_task_select]['DATABASE_NAME'].unique()
        schema_name = data[data['NAME'] == execute_task_select]['SCHEMA_NAME'].unique()

        task_to_be_executed = database_name + "." + schema_name + "." + execute_task_select


        if st.button("Execute Task"):
            st.write("we are here")
            print("EXECUTE TASK " + task_to_be_executed[0])
            conn.execute_string("EXECUTE TASK " + task_to_be_executed[0])
            st.write('Task Executed Successfully. Please check your Snowflake instance for more details.')

        st.write(
            'Below is the run history for the task. Scroll down to execute. Once executed, you can track the status in your Snowflake Account.')
        run_task_list_res = data.loc[data['NAME'] == execute_task_select]
        AgGrid(run_task_list_res, theme='material')


        return task_to_be_executed

    task_to_be_execute = run_task_list(task_hist)



# TAB definition END

# Sidebar definition START

with st.sidebar:
    st.image('task.png', width=150)

    # st.metric(label="Run Statistics", value="10 Success", delta="5 %")
    if st.button('Refresh Task Data?'):
        load_data_task_list.clear()
        load_data_task_hist.clear()
        task_list, load_dt_list = load_data_task_list()
        task_hist, load_dt_hist = load_data_task_hist()
        st.sidebar.info('Data is loaded from Snowflake. If you want to reload the task data again, please click here!')
        time.sleep(1)

    st.sidebar.info(load_dt_list, icon="🕒")

# download_data_task_list()
st.sidebar.markdown(
    """


**Welcome!** This is an unofficial Task Manager for Snowflake Data Cloud. The application can be used to:

**❄ View Task Statistics.**

**❄ See Task List.**

**❄ See Execution History.**

**❄ Execute a Task Ad hoc.**

"""
)
st.sidebar.title("Open Code")
st.sidebar.info(
    "This an weekend project and you are very welcome to use it as it. "
    "No gurantee. "
    "[source code](https://github.com/MarcSkovMadsen/awesome-streamlit). "
)
st.sidebar.title("About")
st.sidebar.info(
    """
    Created by [Sudhendu Pandey](https://sudhendu.com/), Principal Architect at [KIPI.BI](https://kipi.bi).
"""
)

# Sidebar definition END
