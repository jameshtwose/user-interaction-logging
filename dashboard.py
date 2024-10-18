import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go


@st.cache_data(show_spinner="Getting Data", ttl=3600)
def get_data():
    sales_by_country = pd.DataFrame(
        {
            "country": [
                "United States",
                "United Kingdom",
                "France",
                "Germany",
                "Italy",
                "Spain",
                "Canada",
                "Australia",
                "Japan",
                "China",
            ],
            "sales": [
                5000,
                3200,
                2900,
                4100,
                2300,
                2100,
                2500,
                2600,
                4500,
                7000,
            ],
        }
    )

    return sales_by_country


@st.cache_data(show_spinner="Awaiting response from model", ttl=3600)
def get_chat_response(
    data: pd.DataFrame, question_for_agent: str
):
    chat_prompt = f"Based on the sales data below, {question_for_agent}\n\n{data}"
    new_body = {
        "messages": [
            {"role": "user", "content": "Put yourself in the shoes of a data scientist"},
            {"role": "user", "content": chat_prompt},
        ],
        "model": "",
    }

    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json=new_body,
    )
    return response.json().get("choices")[0].get("message").get("content")


# configure the page
st.set_page_config(
    page_title="Dashboard",
    page_icon=":sparkles:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

df = get_data()

st.title("Dashboard")
st.write("This is a dashboard for the sales data")
st.dataframe(df.T)
question_for_agent = st.text_input(
    "Ask a question based on the data",
    "Which are the bottom 5 countries by sales?",
)

if st.button("Ask"):
    print(question_for_agent)
    st.write(question_for_agent)
    result = get_chat_response(
        data=df,
        question_for_agent=question_for_agent,
    )
    st.code(result)

code_to_execute = st.text_input("Enter code to execute", "")
if st.button("Execute"):
    print(code_to_execute)
    if "fig = " in code_to_execute:
        exec(code_to_execute)
        st.plotly_chart(fig)
    else:
        exec(f"result={code_to_execute}")
        st.write(result)