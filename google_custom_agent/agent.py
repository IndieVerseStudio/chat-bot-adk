from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name = "google_custom_agent",
    model = "gemini-2.0-flash-exp",
    description = "An agent that can perform Google searches and return results.",
    instruction="Answer the question using the Google Search tool.",
    tools = [google_search],
)