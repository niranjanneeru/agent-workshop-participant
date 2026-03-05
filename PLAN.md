# Workshop Plan

## Step 0: Simple agent

**Goal:** A minimal runnable graph and agent that the Streamlit app can call.

- Define state (e.g. `messages`).
- Add one LLM node (e.g. simple chat completion).
- Build the graph and compile it.
- Create an agent class with `chat()` that invokes the graph.
- Replace the stub in the app with your agent.

**By the end you should have:** State (messages), one LLM node, builder, one agent class with `chat()`. Stub in app replaced; run and verify in Streamlit.

---

**Next:** Add DB tools to your agent so it can answer questions with real data.
