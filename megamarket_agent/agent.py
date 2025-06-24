from google.adk.agents import Agent

from .prompt import AGENT_PROMPT
from .tools import search_product, create_order, get_order, prepare_order
from .out_of_scope_agent import out_of_scope_agent


root_agent = Agent(
    model="gemini-2.0-flash",
    name="Customer_service_agent",
    description="An intelligent assistant designed to help customers with product inquiries and order placement in the Mega Market supermarket system. It ensures efficient and polite interactions, providing clear instructions and maintaining language consistency with the customer.",
    instruction=AGENT_PROMPT,
    tools=[search_product, prepare_order, create_order, get_order],
    sub_agents=[out_of_scope_agent],
)
