"""
rpcsource.py
============
BlockSource que obtiene bloques por JSON-RPC y los entrega en el mismo
formato que BlkFileSource (diccionario con 'height', 'hash', 'txs').

• Si el nodo devuelve el error «-28 Verifying blocks…», se lanza
  NodeSyncing para que la CLI pueda hacer fallback a blk*.dat.

Dependencia:  python-bitcoinrpc   (añádela en pyproject.toml)
"""

from __future__ import annotations

import binascii
from typing import Dict, Iterable, Optional

from bitcoin.core import CBlock
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException


class NodeSyncing(RuntimeError):
    """El nodo RPC todavía está arrancando / verificando (-28)."""


# -------------------------------------------------------------------------
def _safe_rpc(method, *args):
    """Envuelve una llamada RPC detectando el código -28."""
    try:
        return method(*args)
    except JSONRPCException as exc:
        if exc.error.get("code") == -28:
            raise NodeSyncing(str(exc)) from exc
        raise


# -------------------------------------------------------------------------
class RpcSource:
    """BlockSource que rinde bloques exactos mediante JSON-RPC."""

    def __init__(
        self,
        rpc_url: str,
        start_height: int | None = None,
        end_height: int | None = None,
        hashes: Optional[list[str]] = None,
    ) -> None:
        self.rpc = AuthServiceProxy(rpc_url)
        self.start = start_height
        self.end = end_height
        self.hashes = hashes

    # ------------------------------------------------------------------ #
    def __iter__(self) -> Iterable[Dict]:
        # ----- Caso 1: lista de hashes explícitos ----------------------
        if self.hashes:
            for h in self.hashes:
                yield self._by_hash(h)
            return

        # ----- Caso 2: rango de alturas --------------------------------
        if self.start is None or self.end is None:
            raise ValueError(
                "Con --rpc necesitas --start-height y --end-height o bien --hash."
            )

        for h in range(self.start, self.end + 1):
            blk_hash = _safe_rpc(self.rpc.getblockhash, h)
            yield self._by_hash(blk_hash)

    # ------------------------------------------------------------------ #
    def _by_hash(self, blk_hash: str) -> Dict:
        """Devuelve el bloque {height, hash, txs[]} para el hash dado."""
        raw_hex = _safe_rpc(self.rpc.getblock, blk_hash, 0)  # 0 = hex
        raw = binascii.unhexlify(raw_hex)
        block = CBlock.deserialize(raw)
        height = _safe_rpc(self.rpc.getblockheader, blk_hash)["height"]

        return {
            "height": height,
            "hash": blk_hash,
            "txs": [tx.serialize().hex() for tx in block.vtx],
        }
