from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# Model Initialization
llm = ChatOpenAI(model = "gpt-4o-mini", temperature=0)


# First Agent: Search Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )
# Second Agent: reader Agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )

# Writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

    Topic: {topic}

    Research Gathered:
    {research}

    Structure the report as:
    - Introduction
    - Key Findings (minimum 3 well-explained points)
    - Conclusion
    - Sources (list all sources used in the research)

    Be detailed, factual and professional."""), 
])

writer_chain = writer_prompt | llm | StrOutputParser()

# Critic chain 
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructure research critic. Be honest and specific."),
    ("human", """Review the researhc report below and evaluate it strictly.
    Report:
    {report}
    
    Respond in this exact format:
    Score: X/10
    
    Strengths:
    - ...
    - ...
    
    Areas for Improvement:
    - ...
    - ...

    One line verdict:
    ...
    """),
])

critic_chain = critic_prompt | llm | StrOutputParser()