# tests/test_http_vs_rpc.py
"""
Comprueba que el bloque descargado por RPC y por la API HTTP de mempool.space
coinciden (mismo hash) para un conjunto de alturas.
"""

import pytest
from framework_bt.rpcsource     import RpcSource
from framework_bt.mempoolsource import MempoolApiSource

# --- ajusta a tu entorno ----------------------------------------
RPC_URL   = "http://jdom:900723@127.0.0.1:8332"
HEIGHTS   = [0, 100000, 500000, 790000]      # ← alturas a chequear
# ----------------------------------------------------------------

@pytest.mark.parametrize("height", HEIGHTS)
def test_http_vs_rpc(height):
    # -------- RPC ----------
    rpc_src = RpcSource(RPC_URL, start_height=height, end_height=height)
    blk_rpc = next(iter(rpc_src))

    # ------- HTTP ----------
    http_src = MempoolApiSource(start_height=height, end_height=height, delay=0)
    blk_http = next(iter(http_src))

    # -------- asserts -------
    assert blk_rpc["height"] == blk_http["height"] == height
    assert blk_rpc["hash"]   == blk_http["hash"], (
        f"Hashes distintos para altura {height}: "
        f"{blk_rpc['hash']} (RPC) vs {blk_http['hash']} (HTTP)"
    )
