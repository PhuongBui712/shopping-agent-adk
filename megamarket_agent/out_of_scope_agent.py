from typing_extensions import override, AsyncGenerator

from google.genai import types
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext

DEFAULT_MSG = """
### ***Bạn đã vi phạm chính sách sử dụng trợ lý ảo thông minh của chúng tôi, trợ lý ảo chỉ có thể hỗ trợ bạn các thông tin về sản phẩm và đặt hàng, \
vui lòng tuân thủ qui định để tiếp tục trò chuyện với trợ lý ảo***
"""


class OutOfScopeAgent(BaseAgent):
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=DEFAULT_MSG)]),
        )


out_of_scope_agent = OutOfScopeAgent(
    name="out_of_scope_agent",
    description="An agent designed to handle interactions that fall outside the predefined scope of product inquiries and order placements. It ensures users are informed about the limitations of the virtual assistant's capabilities and encourages compliance with usage policies.",
)
