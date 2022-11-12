# snowflake-task-manager-unofficial
The Streamlit App flow

On a high level, below is the flow of the code. 
Create a Snowflake connection (how).
Execute Snowflake SQL Statements.
Cleanse the response and store it in a data frame into CSV (this is done to avoid calling Snowflake every time someone interacts with the application, saving credits).
Read the CSVs and then use various Streamlit features to display stats, tables, take actions, etc.
Anytime you want to get the latest data from Snowflake, you can use the button 'Refresh Data' to get the latest snapshot from Snowflake.

Snowflake Task Manager with Streamlit: Features
Once connected to your Snowflake environment, the Streamlit application can:
❄ View Task Statistics.
❄ See Task List.
❄ See Execution History.
❄ Execute a Task Ad hoc.
Code Summary
The entire code-base is available on git here. Below is just a gist of what we do and how you can use the code.
Imports (the usuals)
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
Connecting to Snowflake and fetching data
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
Defining the tabs. 
Each tab is a container on the Streamlit UI.
# TAB definition START
tab1, tab2, tab3, tab4 = st.tabs(["📈 TASK SUMMARY", "📜 TASK LIST", "🗃 TASK HISTORY", "🏃 EXECUTE TASK"])
The Final Product

Hold it! Wait for it! Here we go!

Running this in your Snowflake Environment?

Please note this code is not production ready. 
You can easily run this for your Snowflake environment. Below are the steps:
Setup Python and install of the modules which are part of imports.
In the .streamlit directory, edit the secrets.toml connection details. Here is how. Note never check-in your secrets.toml file in public git repositories to avoid compromise.
Run the below command: streamlit run .\SnowTaskManager.py
If all is good, your Streamlit should start on your http://localhost:8501/ 

The Next Steps:
As mentioned, this might not be the cleanest code, so first thing first, I will clean the repo and code flow a bit. I would add folders and move things around a bit. Pagination is another in the list.
Few new features to add would be to option to create a task directly from Streamlit, have a tab/section  dedicated to the failed task, and ability to re-trigger it. I wish there was some easy way to visualize DAG in Python or Streamlit. If yes, we can create dags as well!
I would like to thank my colleagues at Kipi for helping me! Sumit and Abhijeet!
