import os
import certifi
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()

WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")


@tool
def get_weather_data(city: str) -> str:
    """Extra weather data for a given city using the Weatherstack API."""
    url = (
        f"https://api.weatherstack.com/current?"
        f"access_key={WEATHERSTACK_API_KEY}&query={city}"
    )
    data = requests.get(url).json()

    if "current" not in data:
        return f"Could not retrieve weather data for {city}. Please check the city name and try again."

    return (
        f"City: {city}\n"
        f"Temperature: {data['current']['temperature']}°C\n"
        f"Weather: {data['current']['weather_descriptions'][0]}\n"
        f"Humidity: {data['current']['humidity']}%\n"
    )


@st.cache_resource
def build_agent_executor() -> AgentExecutor:
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    tools = [TavilySearchResults(max_results=2), get_weather_data]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True)


st.set_page_config(page_title="LangChain Agent", page_icon="🤖")
st.title("🤖 LangChain Agent")
st.caption("A ReAct agent with web search (Tavily) and weather (Weatherstack).")

missing = [
    k for k in ("OPENAI_API_KEY", "TAVILY_API_KEY", "WEATHERSTACK_API_KEY")
    if not os.getenv(k)
]
if missing:
    st.warning(f"Missing environment variables in .env: {', '.join(missing)}")

with st.sidebar:
    st.header("Chat")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask me anything, e.g. 'What's the weather in Paris?'"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            callback = StreamlitCallbackHandler(st.container())
            result = build_agent_executor().invoke(
                {"input": question}, {"callbacks": [callback]}
            )
            answer = result["output"]
        except Exception as e:
            answer = f"Sorry, something went wrong: {e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
