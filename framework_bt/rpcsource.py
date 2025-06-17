"""
rpcsource.py
============
BlockSource that retrieves blocks via JSON-RPC and returns them in the same
format as BlkFileSource (dictionary with 'height', 'hash', 'txs').

• If the node returns the error “-28 Verifying blocks…”, a NodeSyncing
  exception is raised so that the CLI can fallback to blk*.dat.
"""

from __future__ import annotations

import binascii
from typing import Dict, Iterable, Optional

from bitcoin.core import CBlock
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException


class NodeSyncing(RuntimeError):
    """The RPC node is still starting up / verifying (-28)."""


# -------------------------------------------------------------------------
def _safe_rpc(method, *args):
    """Wraps an RPC call, detecting error code -28."""
    try:
        return method(*args)
    except JSONRPCException as exc:
        if exc.error.get("code") == -28:
            raise NodeSyncing(str(exc)) from exc
        raise


# -------------------------------------------------------------------------
class RpcSource:
    """BlockSource that yields full blocks via JSON-RPC."""

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
        # ----- Case 1: explicit list of hashes -------------------------
        if self.hashes:
            for h in self.hashes:
                yield self._by_hash(h)
            return

        # ----- Case 2: range of block heights --------------------------
        if self.start is None or self.end is None:
            raise ValueError(
                "With --rpc you must specify --start-height and --end-height or --hash."
            )

        for h in range(self.start, self.end + 1):
            blk_hash = _safe_rpc(self.rpc.getblockhash, h)
            yield self._by_hash(blk_hash)

    # ------------------------------------------------------------------ #
    def _by_hash(self, blk_hash: str) -> Dict:
        """Returns a block {height, hash, txs[]} for the given hash."""
        raw_hex = _safe_rpc(self.rpc.getblock, blk_hash, 0)  # 0 = hex response
        raw = binascii.unhexlify(raw_hex)
        block = CBlock.deserialize(raw)
        height = _safe_rpc(self.rpc.getblockheader, blk_hash)["height"]

        return {
            "height": height,
            "hash": blk_hash,
            "txs": [tx.serialize().hex() for tx in block.vtx],
        }
