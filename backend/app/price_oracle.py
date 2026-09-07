"""
LEATrace Price Oracle — Production.

Real-time cryptocurrency price resolution using CoinGecko free API.
In-memory cache with configurable TTL. No hardcoded prices.

PRODUCTION INVARIANTS:
- Never returns hardcoded prices (no "$3500 ETH").
- Returns None when price is unavailable.
- Cache TTL of 5 minutes to balance freshness and rate limits.
"""

import time
import logging
from typing import Dict, Optional

from .connection_pool import connection_pool

logger = logging.getLogger("leatrace.price_oracle")

# CoinGecko IDs for supported chain tokens
COINGECKO_IDS = {
    "ETH": "ethereum",
    "BTC": "bitcoin",
    "MATIC": "matic-network",
    "BNB": "binancecoin",
    "AVAX": "avalanche-2",
    "SOL": "solana",
    "LTC": "litecoin",
    "DOGE": "dogecoin",
    "TRX": "tron",
    "USDT": "tether",
    "USDC": "usd-coin",
}

# Chain ID → native token symbol
CHAIN_TOKENS = {
    "ethereum": "ETH",
    "polygon": "MATIC",
    "bnb": "BNB",
    "avalanche": "AVAX",
    "arbitrum": "ETH",
    "optimism": "ETH",
    "base": "ETH",
    "bitcoin": "BTC",
    "solana": "SOL",
    "litecoin": "LTC",
    "dogecoin": "DOGE",
    "tron": "TRX",
}


class PriceOracle:
    """
    Cryptocurrency price oracle using CoinGecko free API.
    Caches prices in memory with configurable TTL.
    """

    def __init__(self, cache_ttl_seconds: float = 300.0):
        self._cache: Dict[str, float] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = cache_ttl_seconds
        self._coingecko_url = "https://api.coingecko.com/api/v3"

    def get_price_usd(self, symbol: str) -> Optional[float]:
        """
        Gets the current USD price for a token symbol (e.g., 'ETH', 'BTC').
        Returns None if unavailable.
        """
        symbol_upper = symbol.upper()

        # Check cache
        if symbol_upper in self._cache:
            if time.time() - self._cache_timestamps.get(symbol_upper, 0) < self._cache_ttl:
                return self._cache[symbol_upper]

        # Look up CoinGecko ID
        cg_id = COINGECKO_IDS.get(symbol_upper)
        if not cg_id:
            return None

        # Fetch from CoinGecko
        try:
            url = f"{self._coingecko_url}/simple/price?ids={cg_id}&vs_currencies=usd"
            data = connection_pool.get_json(url, timeout=5)
            if data and cg_id in data:
                price = data[cg_id].get("usd")
                if price is not None:
                    self._cache[symbol_upper] = float(price)
                    self._cache_timestamps[symbol_upper] = time.time()
                    return float(price)
        except Exception as e:
            logger.debug(f"Price fetch failed for {symbol_upper}: {e}")

        # Return stale cache if available
        if symbol_upper in self._cache:
            logger.debug(f"Returning stale cached price for {symbol_upper}")
            return self._cache[symbol_upper]

        return None

    def get_chain_price_usd(self, chain_id: str) -> Optional[float]:
        """Gets the USD price for a chain's native token."""
        symbol = CHAIN_TOKENS.get(chain_id)
        if not symbol:
            return None
        return self.get_price_usd(symbol)

    def convert_to_usd(self, amount: float, symbol: str) -> Optional[float]:
        """Converts a token amount to USD. Returns None if price unavailable."""
        price = self.get_price_usd(symbol)
        if price is None:
            return None
        return round(amount * price, 2)

    def convert_chain_to_usd(self, amount: float, chain_id: str) -> Optional[float]:
        """Converts a native token amount to USD by chain ID."""
        price = self.get_chain_price_usd(chain_id)
        if price is None:
            return None
        return round(amount * price, 2)

    def fetch_all_prices(self) -> Dict[str, Optional[float]]:
        """Fetches prices for all supported tokens. Returns {symbol: price_usd}."""
        ids = ",".join(COINGECKO_IDS.values())
        try:
            url = f"{self._coingecko_url}/simple/price?ids={ids}&vs_currencies=usd"
            data = connection_pool.get_json(url, timeout=10)
            if data:
                for symbol, cg_id in COINGECKO_IDS.items():
                    if cg_id in data and "usd" in data[cg_id]:
                        price = float(data[cg_id]["usd"])
                        self._cache[symbol] = price
                        self._cache_timestamps[symbol] = time.time()
        except Exception as e:
            logger.warning(f"Bulk price fetch failed: {e}")

        return {symbol: self._cache.get(symbol) for symbol in COINGECKO_IDS}

    def get_cached_prices(self) -> Dict[str, Optional[float]]:
        """Returns all cached prices without fetching."""
        return dict(self._cache)


# Singleton
price_oracle = PriceOracle()
