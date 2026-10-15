# 🔎 Research Studio — LangChain Multi-Agent Research System

A multi-agent pipeline that takes a topic and produces a researched, structured report — then critiques it. Four specialized steps (search → read → write → critique) are orchestrated with [LangChain](https://python.langchain.com/) and exposed through a [Streamlit](https://streamlit.io/) UI or a simple CLI script.

## Features

- **Search agent** – a tool-calling agent that queries the web via [Tavily](https://tavily.com/).
- **Reader agent** – a tool-calling agent that picks the most relevant URL and scrapes it, with a three-stage extraction fallback (trafilatura → readability → BeautifulSoup).
- **Writer chain** – turns the gathered research into a report (Introduction, Key Findings, Conclusion, Sources).
- **Critic chain** – scores the report out of 10 and lists strengths and areas for improvement.
- **Streamlit UI** – live step-by-step progress, run history, report / critique / sources / logs tabs, and Markdown download.

## Architecture

```
            ┌──────────────┐   search results   ┌──────────────┐
 topic ───▶ │ Search Agent │ ─────────────────▶ │ Reader Agent │
            │  web_search  │                    │  scrape_url  │
            └──────────────┘                    └──────┬───────┘
                (Tavily)                               │ scraped content
                                                       ▼
            ┌──────────────┐      report        ┌──────────────┐
 feedback ◀─│ Critic Chain │ ◀───────────────── │ Writer Chain │
            └──────────────┘                    └──────────────┘
```

The pipeline is a sequential workflow that passes a shared `state` dict from step to step (`search_results` → `scraped_content` → `report` → `feedback`). All steps share one LLM (`gpt-4o-mini`, temperature 0).

| Layer | File | Responsibility |
| --- | --- | --- |
| Tools | [src/tools/tools.py](src/tools/tools.py) | `web_search` (Tavily) and `scrape_url` (robust page extraction) as LangChain `@tool`s |
| Agents | [src/agents/agents.py](src/agents/agents.py) | Builds the search and reader agents (`create_agent`) and the writer / critic prompt chains |
| Pipeline | [src/pipelines/pipeline.py](src/pipelines/pipeline.py) | `run_research_pipeline(topic, on_step=None)` runs the four steps; the optional `on_step` callback drives UI progress |
| UI | [app.py](app.py) | Streamlit front end |
| CLI | [main.py](main.py) | Runs the pipeline once for a hard-coded topic and prints to the console |

## Technologies

| Technology | Used for |
| --- | --- |
| Python 3.11 | Runtime |
| LangChain (`langchain`, `-core`, `-community`, `-openai`) | Agents, tools, prompts, chains (`create_agent` requires LangChain 1.x) |
| OpenAI (`gpt-4o-mini`) | LLM for all steps |
| Tavily | Web search API |
| trafilatura, readability-lxml, BeautifulSoup4, lxml, requests | Web page scraping and content extraction |
| Streamlit | Web UI |
| python-dotenv, rich | Config loading and console output |

## Getting Started

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (or any Python 3.11 environment manager)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Tavily API key](https://app.tavily.com/) (free tier available)

### Installation

```bash
git clone <your-repo-url>
cd learn-agentic-ai/langchain-multi-agent-system

conda create -n langagent python=3.11 -y
conda activate langagent
pip install -r requirements.txt
```

> `create_agent` is only available in LangChain 1.x. If you hit an import error, run `pip install -U "langchain>=1.0" langchain-openai langchain-core`.

### Configuration

Create a `.env` file in this directory (it is git-ignored):

```env
OPENAI_API_KEY=your-openai-key
TAVILIY_API_KEY=your-tavily-key
```

> ⚠️ The Tavily variable is spelled `TAVILIY_API_KEY` (sic) because that is the name [tools.py](src/tools/tools.py) reads. If you correct the spelling in the code, update your `.env` to match.

## Usage

### Web UI (Streamlit)

```bash
streamlit run app.py
```

Open http://localhost:8501, pick an example topic or type your own, and click **Run ▶**. Results appear in the Report, Critic feedback, Sources and Logs tabs. A run takes roughly a minute or two since it makes live search and LLM calls.

### Command line

```bash
python main.py
```

Edit the `topic` variable in [main.py](main.py), or import the pipeline directly:

```python
from src.pipelines.pipeline import run_research_pipeline

state = run_research_pipeline("State of solid-state battery technology")
print(state["report"])
print(state["feedback"])
```

## Deployment

### Streamlit Community Cloud

1. Push the repository to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app, pointing at this folder's `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   OPENAI_API_KEY = "your-openai-key"
   TAVILIY_API_KEY = "your-tavily-key"
   ```
   Streamlit exposes secrets as environment variables, which `python-dotenv`-based code reads fine.

### Docker

Add a `Dockerfile` next to `app.py`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

Build and run, passing keys at runtime rather than baking them into the image:

```bash
docker build -t research-studio .
docker run -p 8501:8501 --env-file .env research-studio
```

The image can then be deployed to any container host (Azure Container Apps, AWS ECS/App Runner, Google Cloud Run, Fly.io, etc.).

## Project Structure

```
langchain-multi-agent-system/
├── app.py                  # Streamlit UI
├── main.py                 # CLI entry point
├── requirements.txt
└── src/
    ├── agents/agents.py        # Search/reader agents, writer/critic chains
    ├── pipelines/pipeline.py   # Sequential orchestration
    └── tools/tools.py          # web_search, scrape_url
```

## Customization

- **Change the model** – edit the `ChatOpenAI(model=...)` line in [src/agents/agents.py](src/agents/agents.py).
- **Tune search** – adjust `max_results` or the snippet length in `web_search`.
- **Change report format or critique rubric** – edit `writer_prompt` / `critic_prompt`.
- **Add a step** – add a function to the pipeline and call `on_step(index, "start"/"done", state)` around it (and add an entry to `STEPS` in `app.py` for the UI).

## Contributing

Contributions are welcome. Fork the repo, create a feature branch, and open a pull request describing your change.

## License

No license has been specified yet. Add a `LICENSE` file (e.g. MIT) before distributing.
