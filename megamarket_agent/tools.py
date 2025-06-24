import os
from typing import List, Optional, Dict, Any

from .order_handler import OrderHandler
from .elasticsearch import ProductSearcher


product_searcher = ProductSearcher(
    host=os.getenv("ELASTICSEARCH_HOST"),
    api_key=os.getenv("ELASTICSEARCH_API_KEY"),
    index_name=os.getenv("ELASTIC_PRODUCT_INDEX"),
)


order_handler = OrderHandler(
    uri=os.getenv("MONGODB_URI"), database="mega-market-database", collection="orders"
)


async def search_product(query_text: str, size: int = 5):
    """
    Searches for products based on the provided query text.

    Args:
    - `query_text` (str): The text query to search for products.
    - `size` (int, optional): The number of search results to return. Defaults to 5.

    Returns:
    - A list of products matching the search criteria.
    """
    return await product_searcher.search_products(query_text, size)


async def prepare_order(
    customer_name: str,
    customer_phone_number: str,
    delivery_address: str,
    ordered_products: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Prepares an order with the provided customer and product details. This function should be used before finalizing an order with `create_order`.

    Args:
    - `customer_name` (str): The name of the customer placing the order.
    - `customer_phone_number` (str): The phone number of the customer.
    - `delivery_address` (str): The address where the order should be delivered.
    - `ordered_products` (List[Dict[str, Any]]): A list of ordered products, each containing:
        - `product_id`: A string representing the unique identifier of the product.
        - `quantity`: A float indicating the number of units of the product to be ordered. If `buy_combo` is true, this represents the number of combos.
        - `buy_combo`: A boolean indicating whether the customer buys a combo or not.
        - `combo_price`: A float representing the price of the product if the customer purchased a combo.

    Returns:
    - A dictionary containing the prepared order details.
    """
    await order_handler.initialize()
    return await order_handler._prepare_order(
        customer_name=customer_name,
        customer_phone_number=customer_phone_number,
        delivery_address=delivery_address,
        ordered_products=ordered_products,
    )


async def create_order(order_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Use `create_order` only after using the `prepare_order` tool and the user has confirmed the final order data. This tool finalizes the order creation process.

    Args:
    - `order_data` (Dict[str, Any]): A dictionary containing the finalized order data, which is the output of the `prepare_order` tool.

    Returns:
    - A dictionary indicating the success or failure of the order creation process.

    Example:
    - User: "Thông tin đơn hàng chính xác" (confirmation of order data)
    """
    await order_handler.initialize()
    order_result = await order_handler.create_order(order_data)

    return {"status": "success" if order_result else "failed"}


async def get_order(
    order_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone_number: Optional[str] = None,
):
    """
    Use `get_order` to retrieve order details based on provided identifiers. You can search for an order using the order ID, customer name, or customer's phone number.

    Args:
    - `order_id` (Optional[str], optional): The unique identifier of the order. Defaults to None.
    - `customer_name` (Optional[str], optional): The name of the customer who placed the order. Defaults to None.
    - `customer_phone_number` (Optional[str], optional): The phone number of the customer who placed the order. Defaults to None.

    Returns:
    - The order details matching the provided search criteria.

    Note:
    - At least one of the parameters: `order_id`, `customer_name`, or `customer_phone_number` must be provided to perform a search.
    """
    await order_handler.initialize()

    return await order_handler.get_order(
        order_id=order_id,
        customer_name=customer_name,
        customer_phone_number=customer_phone_number,
    )
