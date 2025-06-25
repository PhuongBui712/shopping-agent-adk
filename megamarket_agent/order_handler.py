import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from .elasticsearch import ProductSearcher
from .utils import generate_id_from_str


class OrderedProduct(TypedDict):
    product_id: str
    quantity: float


class OrderHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OrderHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, uri: str, *, database: str, collection: str) -> None:
        if not hasattr(self, "initialized"):
            self.uri = uri
            self.database_name = database
            self.collection_name = collection
            self.mongo_collection: Optional[AsyncCollection] = None
            self.initialized = True

    @property
    def product_searcher(self):
        return ProductSearcher()

    async def initialize(self):
        if self.mongo_collection is None:
            self.mongo_collection = await self._init_collection(
                self.uri,
                database_name=self.database_name,
                collection_name=self.collection_name,
            )

    async def _init_collection(
        self, uri: str, *, database_name: str, collection_name: str
    ) -> AsyncCollection:
        client = AsyncMongoClient(uri)
        database = client[database_name]
        if collection_name not in (await database.list_collection_names()):
            collection = await database.create_collection(collection_name)
        else:
            collection = database[collection_name]

        return collection

    async def get_order(
        self,
        *,
        order_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone_number: Optional[str] = None,
    ):
        if not (order_id or customer_name or customer_phone_number):
            raise ValueError(
                "Either customer_name or customer_phone_number must be provided."
            )

        search_fields = {}
        if order_id:
            search_fields["order_id"] = order_id
        else:
            if customer_name:
                search_fields["customer_name"] = customer_name
            if customer_phone_number:
                search_fields["customer_phone_number"] = customer_phone_number

        return await self.mongo_collection.find(search_fields)

    async def _prepare_order(
        self,
        *,
        customer_name: str,
        customer_phone_number: str,
        delivery_address: str,
        ordered_products: List[OrderedProduct],
    ) -> List[Dict[str, Any]]:
        # create order record
        # get products data
        products_data = await asyncio.gather(
            *[
                self.product_searcher.get_product_by_id(product["product_id"])
                for product in ordered_products
            ]
        )
        products: List[Dict[str, Any]] = []
        total_amount = 0
        for product, data in zip(ordered_products, products_data):
            data_source = data["_source"]
            if product.get("buy_combo"):
                total = (
                    product.get("combo_price", data_source["final_price"])
                    * product["quantity"]
                )

                products.append(
                    {
                        "product_id": data_source["product_id"],
                        "product_name": data_source.get(
                            "product_combo", data_source.get("product_name")
                        ),
                        "unit_price": data_source["original_price"],
                        "discount": data_source["discount"],
                        "quantity": product["quantity"],
                        "total": total,
                    }
                )
            else:
                total = (
                    product["quantity"]
                    * data_source["original_price"]
                    * ((100 - float(data_source.get("discount", 0) or 0.0)) / 100)
                )

                products.append(
                    {
                        "product_id": data_source["product_id"],
                        "product_name": data_source["product_name"],
                        "unit_price": data_source["original_price"],
                        "discount": data_source["discount"],
                        "quantity": product["quantity"],
                        "total": total,
                    }
                )

            total_amount += total

        # create a record
        order_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return {
            "order_id": generate_id_from_str(f"{customer_name}-{order_date}"),
            "order_date": order_date,
            "customer_name": customer_name,
            "customer_number": customer_phone_number,
            "dilivery_address": delivery_address,
            "total_amount": total_amount,
            "products": products,
            "order_status": "confirmed",  # <order status, include 4 status: not confirmed, confirmed, in transit, being delivered, delivered>
        }

    async def create_order(self, order: Dict[str, Any]) -> bool:
        # upload to mongo
        try:
            # await self.mongo_collection.insert_one(order)
            return True
        except Exception:
            return False
