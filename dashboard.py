from pandasai import Agent
from pandasai.llm.local_llm import LocalLLM
import pandas as pd
import streamlit as st

ollama_llm = LocalLLM(api_base="http://localhost:11434/v1", model="codellama")
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
        "sales": [5000, 3200, 2900, 4100, 2300, 2100, 2500, 2600, 4500, 7000],
    }
)
agent = Agent(sales_by_country, config={"llm": ollama_llm})

# configure the page
st.set_page_config(
    page_title="Dashboard",
    page_icon=":sparkles:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Dashboard")
st.dataframe(sales_by_country)
question_for_agent = st.text_input("Ask a question based on the data", "Which are the bottom 5 countries by sales?")
if st.button("Ask"):
    print(question_for_agent)
    st.write(question_for_agent)
    result = agent.chat(question_for_agent)
    print(result)
    st.write(result)
