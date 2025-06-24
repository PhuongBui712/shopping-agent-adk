from typing import List, Dict, Any, Optional

from elasticsearch import AsyncElasticsearch


class ProductSearcher:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ProductSearcher, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: str = "product-data",
    ):
        if not hasattr(self, "initialized"):  # Ensure initialization happens only once
            """
            Initialize Elasticsearch connection
            
            Args:
                host: Elasticsearch host
                index_name: Name of the index containing products
            """
            self.es = AsyncElasticsearch(hosts=host, api_key=api_key)
            self.index_name = index_name
            self.initialized = True

    async def get_product_by_id(self, id: str) -> List[Dict[str, Any]]:
        return await self.es.get(index=self.index_name, id=id)

    async def search_products(
        self, query_text: str, size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for products using case-insensitive multi-field search

        Args:
            query_text: Search term (e.g., "khổ qua", "thịt", "Khổ qua dồn thịt")
            size: Maximum number of results to return

        Returns:
            List of matching products with their scores
        """
        # Build multi-field search query with case insensitive matching
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        # Exact match on product name (highest priority)
                        {
                            "match": {
                                "product_name": {
                                    "query": query_text,
                                    "boost": 3.0,
                                    "fuzziness": "AUTO",
                                }
                            }
                        },
                        # Match in product description (if not empty)
                        {
                            "match": {
                                "product_description": {
                                    "query": query_text,
                                    "boost": 2.0,
                                }
                            }
                        },
                        # Match in product unit (for unit-based searches like "ký", "gram")
                        {
                            "match": {
                                "product_unit": {"query": query_text, "boost": 1.0}
                            }
                        },
                        # Match in product combo description (if available)
                        {
                            "match": {
                                "product_combo": {"query": query_text, "boost": 1.5}
                            }
                        },
                        # Wildcard search for partial matches on product name
                        {
                            "wildcard": {
                                "product_name.keyword": {
                                    "value": f"*{query_text.lower()}*",
                                    "boost": 1.0,
                                    "case_insensitive": True,
                                }
                            }
                        },
                        # Prefix search for product_id (useful for exact product lookups)
                        {"prefix": {"product_id": {"value": query_text, "boost": 2.5}}},
                    ],
                    "minimum_should_match": 1,
                    # Filter out products with empty descriptions if needed
                    "filter": [{"exists": {"field": "product_name"}}],
                }
            },
            "size": size,
            "sort": [
                "_score",
                {
                    "final_price": {"order": "asc"}
                },  # Sort by final price instead of price
                {
                    "product_rate": {"order": "desc", "missing": "_last"}
                },  # Secondary sort by rating if available
            ],
        }

        try:
            response = await self.es.search(index=self.index_name, body=search_body)

            results = []
            for hit in response["hits"]["hits"]:
                product = hit["_source"]
                product["_score"] = hit["_score"]
                product["_id"] = hit["_id"]
                results.append(product)

            return results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    async def search_by_category(
        self, category: str, size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search products by category (case-insensitive)

        Args:
            category: Category to search for
            size: Maximum number of results

        Returns:
            List of products in the category
        """
        search_body = {
            "query": {"match": {"category": {"query": category, "fuzziness": "AUTO"}}},
            "size": size,
            "sort": [{"price": {"order": "asc"}}],
        }

        try:
            response = await self.es.search(index=self.index_name, body=search_body)

            results = []
            for hit in response["hits"]["hits"]:
                product = hit["_source"]
                product["_id"] = hit["_id"]
                results.append(product)

            return results

        except Exception as e:
            print(f"Category search error: {e}")
            return []

    async def suggest_products(self, query_text: str, size: int = 5) -> List[str]:
        """
        Get product name suggestions for autocomplete

        Args:
            query_text: Partial product name
            size: Number of suggestions

        Returns:
            List of suggested product names
        """
        search_body = {
            "suggest": {
                "product_suggest": {
                    "prefix": query_text.lower(),
                    "completion": {
                        "field": "product_name.suggest",
                        "size": size,
                        "skip_duplicates": True,
                    },
                }
            }
        }

        try:
            response = await self.es.search(index=self.index_name, body=search_body)
            suggestions = []

            for option in response["suggest"]["product_suggest"][0]["options"]:
                suggestions.append(option["text"])

            return suggestions

        except Exception as e:
            print(f"Suggestion error: {e}")
            return []
