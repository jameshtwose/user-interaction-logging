import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import os
from opensearchpy import OpenSearch


@st.cache_data(show_spinner="Getting Data", ttl=3600)
def get_data(limit: int = 10):
    """Get data from OpenSearch and return it as a melted DataFrame.

    Parameters
    ----------
    limit : int
        The number of documents to retrieve from OpenSearch.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the data retrieved from Open

    """
    host = "localhost"
    port = 9200
    auth = (
        "admin",
        os.getenv("OPENSEARCH_PASSWORD", "admin"),
    )  # For testing only. Don't store credentials in code.

    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )

    info = client.info()
    print(
        f"Welcome to {info['version']['distribution']} {info['version']['number']}!"
    )

    index_name = "canvas-index"

    # get all documents
    query = {
        "size": limit,
        "query": {
            "match_all": {},
        },
        "sort": [{"timestamp": {"order": "desc"}}],
    }

    response = client.search(body=query, index=index_name)

    print(len(response.get("hits").get("hits")))

    source_df = pd.DataFrame(
        [x["_source"] for x in response.get("hits").get("hits")]
    ).assign(
        **{
            "doc_id": [x["_id"] for x in response.get("hits").get("hits")],
        }
    )

    return source_df.melt(id_vars=["doc_id", "timestamp", "message_type"])


@st.cache_data(show_spinner="Awaiting response from model", ttl=3600)
def get_chat_response(data: pd.DataFrame, question_for_agent: str):
    chat_prompt = f"""
    Based on the log data below, {question_for_agent}
    
    {data.to_dict()}
    """
    if "code" in question_for_agent:
        new_body = {
            "messages": [
                {
                    "role": "user",
                    "content": "Put yourself in the shoes of a data scientist",
                },
                {"role": "user", "content": chat_prompt},
                {
                    "role": "user",
                    "content": "What code would you write to answer this question?",
                },
                {"role": "user", "content": "Use plotly express for plots"},
                {"role": "user", "content": "Please explain your reasoning"},
            ],
            "model": "",
        }
    else:
        new_body = {
            "messages": [
                {
                    "role": "user",
                    "content": "Put yourself in the shoes of a business consultant",
                },
                {
                    "role": "user",
                    "content": chat_prompt,
                },
            ],
            "model": "",
        }

    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json=new_body,
    )
    if response.status_code != 200:
        return response.text
    return response.json().get("choices")[0].get("message").get("content")


# configure the page
st.set_page_config(
    page_title="Dashboard",
    page_icon=":sparkles:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Dashboard")
st.write("This is a dashboard for the log data")
chosen_limit = st.selectbox(
    "Choose the number of documents to retrieve",
    [10, 20, 50, 100, 1000, 10000],
)

df = get_data(limit=chosen_limit)
st.write(f"Data retrieved from OpenSearch row count: {df.shape[0]}")
st.dataframe(df, use_container_width=True, height=200)
st.subheader(
    """Enter python code to execute (for plots begin with "fig = " , else begin with "output = ")"""
)
st.write(
    "Plotly Express code is recommended for plots, for more info see https://plotly.com/python/plotly-express/"
)
code_to_execute_explanation = """
# e.g.
fig = px.bar(
    df.dropna().value_counts(subset=["variable"]).to_frame().reset_index().rename(columns={0: "count"}),
    x="variable",
    y="count",
)
# or 
output = df.dropna().value_counts(subset=["variable"]).to_frame().reset_index().rename(columns={0: "count"})
# or (for multiple lines of code, separate them with a semicolon (;))
variable_counts = df.dropna()['variable'].value_counts();variable_counts_df = pd.DataFrame({'Variable': variable_counts.index, 'Counts': variable_counts.values});fig = px.pie(variable_counts_df, values='Counts', names='Variable', title='Variable Counts in Log Data') 
"""
st.code(code_to_execute_explanation)
code_to_execute = st.text_input("Enter your code", "")
if st.button("Execute"):
    print(code_to_execute)
    if "fig" in code_to_execute:
        exec(code_to_execute)
        st.plotly_chart(fig)
    elif "plt." in code_to_execute:
        exec(code_to_execute)
        st.pyplot(fig)
    else:
        exec(code_to_execute)
        st.write(output)

    # chosen_plot_type = st.selectbox(
    #     "Choose a type of plot",
    #     ["Bar", "Line", "Scatter", "Pie"],
    # )

    # if chosen_plot_type == "Bar":
    fig = px.bar(
        df.dropna()
        .value_counts(subset=["variable"])
        .to_frame()
        .reset_index()
        .rename(columns={0: "count"}),
        x="variable",
        y="count",
    )
#     st.plotly_chart(fig)
st.subheader(
    "Ask a question based on the data (experimental), an LMM will attempt to answer/ generate code for you"
)
question_for_agent = st.text_input(
    "",
    "What are the counts per variable?",
)

if st.button("Ask"):
    print(question_for_agent)
    result = get_chat_response(
        data=df,
        question_for_agent=question_for_agent,
    )
    st.code(result)
