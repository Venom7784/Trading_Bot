from .signer import signed_headers
import asyncio
import logging

class Broker:
    def __init__(self, session, api_key, api_secret):
        self.session = session
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(__name__)

    async def get_balance(self):
        """
        Fetch wallet balance from the API.
        Returns the balance as a float.
        """
        path = "/v2/wallet/balances"
        payload = {}
        headers = signed_headers(self.api_key, self.api_secret, "GET", path, payload)
        async with self.session.get(path, headers=headers) as resp:
            data = await resp.json()
            # Assumes the first result is the relevant asset
            balance_str = data["result"][0]["balance"]
            return float(balance_str)

    async def market(self, side: str, size: float, product_id: int, price: float | None = None, min_balance: float = 0, reduce_only: bool = False):
        """
        Execute a market order.
        
        Args:
            side: "buy" or "sell"
            size: Order size
            product_id: Product ID from the exchange (required)
            price: Current price (optional, not used by real broker)
            min_balance: Minimum balance required to execute order
            reduce_only: Whether the order is reduce-only
        """
        # Check balance before placing order
        if min_balance > 0:
            balance = await self.get_balance()
            if balance < min_balance:
                print(f"Balance too low ({balance} < {min_balance}), stopping the bot.")
                # You can raise an exception or handle bot stop logic here
                raise Exception("Balance below minimum threshold")

        path = "/v2/orders"
        payload = {
            "product_id": product_id,
            "side": side,
            "order_type": "market_order",
            "size": size,
            "reduce_only": reduce_only
        }

        headers = signed_headers(self.api_key, self.api_secret, "POST", path, payload)
        async with self.session.post(path, json=payload, headers=headers) as r:
            return await r.json()

    async def cancel_all(self, symbol: str):
        """
        Cancel all orders for a given symbol.
        
        Args:
            symbol: Trading symbol
        """
        path = f"/v2/orders/all"
        headers = signed_headers(self.api_key, self.api_secret, "DELETE", path, {})
        async with self.session.delete(path, headers=headers) as resp:
            result = await resp.json()
            self.logger.info(f"[CANCEL] All orders for {symbol} cancelled: {result}")
            return result
