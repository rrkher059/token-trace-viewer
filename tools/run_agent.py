import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExporter, SimpleSpanProcessor

# 1. OpenTelemetry JSONL Exporter
class JSONLSpanExporter(SpanExporter):
    def __init__(self, filename="openrouter_trace.jsonl"):
        self.filename = filename

    def export(self, spans):
        with open(self.filename, "a", encoding="utf-8") as f:
            for span in spans:
                f.write(span.to_json() + "\n")
        return True

# 2. Setup Instrumentation
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter("openrouter_trace.jsonl")))
trace.set_tracer_provider(provider)

LangChainInstrumentor().instrument()

# 3. Configure ChatOpenAI for OpenRouter
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0
)

class State(TypedDict):
    messages: list

def planner_step(state: State):
    response = llm.invoke(state["messages"] + [HumanMessage(content="Break down this task: Create a quick 2-step plan to summarize AI trends.")])
    return {"messages": state["messages"] + [response]}

def writer_step(state: State):
    prompt = state["messages"] + [HumanMessage(content="Based on the plan above, write a short 2-sentence summary.")]
    response = llm.invoke(prompt)
    return {"messages": state["messages"] + [response]}

# Build Graph
workflow = StateGraph(State)
workflow.add_node("planner", planner_step)
workflow.add_node("writer", writer_step)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "writer")
workflow.add_edge("writer", END)

app = workflow.compile()

if __name__ == "__main__":
    print("Running agent via OpenRouter...")
    app.invoke({"messages": [HumanMessage(content="You are an AI assistant.")]})
    print("Execution complete! Traces written to 'openrouter_trace.jsonl'.")