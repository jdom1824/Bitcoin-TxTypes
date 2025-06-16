from framework_bt.rpcsource import RpcSource
from framework_bt.blkfile import BlkFileSource
import os

# ---------- RPC TEST ----------
def test_rpc_source():
    rpc_url = "http://jdom:900723@127.0.0.1:8332"
    src = RpcSource(rpc_url, start_height=0, end_height=0)
    blk = next(iter(src))
    assert "txs" in blk
    assert isinstance(blk["txs"], list)
    assert blk["height"] == 0


# ---------- BLKFILE TEST ----------
def test_blkfile_source():
    blk_dir = "/media/jdom-sas/node/Bitcoin/blocks"
    assert os.path.isdir(blk_dir), f"Directory not found: {blk_dir}"

    src = BlkFileSource(blk_dir, start_height=0, end_height=0)
    blk = next(iter(src))
    assert "raw" in blk
    assert isinstance(blk["raw"], bytes)
    assert blk["height"] == 0
