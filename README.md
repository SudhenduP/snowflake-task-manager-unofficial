# snowflake-task-manager-unofficial
The Streamlit App flow

On a high level, below is the flow of the code. 
1. Create a Snowflake connection (how).
2. Execute Snowflake SQL Statements.
3. Cleanse the response and store it in a data frame into CSV (this is done to avoid calling Snowflake every time someone interacts with the application, saving credits).
4. Read the CSVs and then use various Streamlit features to display stats, tables, take actions, etc.
5. Anytime you want to get the latest data from Snowflake, you can use the button 'Refresh Data' to get the latest snapshot from Snowflake.
6. 

# Snowflake Task Manager with Streamlit: Features
Once connected to your Snowflake environment, the Streamlit application can:

❄ View Task Statistics.

❄ See Task List.

❄ See Execution History.

❄ Execute a Task Ad hoc.


# Running this in your Snowflake Environment?

# Please note this code is not production ready. 

You can easily run this for your Snowflake environment. Below are the steps:
1. Setup Python and install of the modules which are part of imports.
2. In the .streamlit directory, edit the secrets.toml connection details. Here is how. Note never check-in your secrets.toml file in public git repositories to avoid compromise.
3. Run the below command: streamlit run .\SnowTaskManager.py
4. If all is good, your Streamlit should start on your http://localhost:8501/ 

#The Next Steps:
As mentioned, this might not be the cleanest code, so first thing first, I will clean the repo and code flow a bit. 

I would add folders and move things around a bit. Pagination is another in the list.

Few new features to add would be to option to create a task directly from Streamlit, have a tab/section  dedicated to the failed task, and ability to re-trigger it. 

I wish there was some easy way to visualize DAG in Python or Streamlit. If yes, we can create dags as well!

I would like to thank my colleagues at Kipi for helping me! Sumit and Abhijeet!
