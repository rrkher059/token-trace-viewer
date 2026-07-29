# tools

`run_agent.py` runs a two-step LangGraph agent through OpenRouter and writes its OpenInference spans to `openrouter_trace.jsonl`, the raw trace `real-trace.jsonl` was derived from.
It needs `pip install langgraph langchain-openai openinference-instrumentation-langchain opentelemetry-sdk` and an `OPENROUTER_API_KEY` environment variable.
It is not part of the tool itself — `ttv.py` and the scripts it imports remain standard-library only.
