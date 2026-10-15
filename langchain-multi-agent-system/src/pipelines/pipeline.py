from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

def run_research_pipeline(topic: str, on_step=None) -> dict:
    """Run the pipeline. `on_step(index, event, state)` is called with event
    "start"/"done" around each of the 4 steps (0=search, 1=read, 2=write, 3=critic)."""
    notify = on_step or (lambda *_: None)
    # Search agent
    state = {}
    notify(0, "start", state)
    print("\n"+"="*50)
    print("step 1: Running Search Agent... ")
    print("="*50)

    search_agent = build_search_agent()
    search_results = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]

    })

    # Research agent
    state["search_results"] = search_results
    notify(0, "done", state)

    print("\n search result: ", state['search_results'])

    print("\n"+"="*50)
    print("step 2: Running Scrape Agent... ")
    print("="*50)

    notify(1, "start", state)
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user", 
                f"Based on the following search results about '{topic}',"
                f"pick the most relevent URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results']}"
        )]
    })

    state['scraped_content'] = reader_result['messages'][-1].content
    print("\nScraped content: \n", state['scraped_content'])
    notify(1, "done", state)

    # Writer chain
    print("\n"+" ="*50)
    print("step 3: Writer is drafting the report...")
    print("="*50)

    notify(2, "start", state)
    research_combined = (
        f"SEARCH RESULTS: \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}"

    )

    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print("\n Final Report\n", state['report'])
    notify(2, "done", state)

    #critic report
    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report")
    print("="*50)

    notify(3, "start", state)
    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })

    print("\n critic report \n", state['feedback'])
    notify(3, "done", state)

    return state
