# tests/test_all_sources.py

import os
import pytest
from framework_bt import extract
from framework_bt.rpcsource import RpcSource
from framework_bt.blkfile import BlkFileSource
from framework_bt.p2psource import P2PSource
from framework_bt.mempoolsource import MempoolApiSource
from framework_bt.classifier import StandardClassifier

RPC_URL     = "http://jdom:900723@127.0.0.1:8332"
BLK_DIR     = os.getenv("BLK_DIR", "/media/jdom-sas/node/Bitcoin/blocks")  
SAMPLE_H    = 800010  
PEER_IP     = "65.109.158.58"

def _collect_utxos(src):
    clf = StandardClassifier()
    return list(extract(src, clf, start_height=SAMPLE_H, end_height=SAMPLE_H))

@pytest.mark.parametrize("src_class, kwargs", [
    (RpcSource,        {"rpc_url": RPC_URL}),
    (BlkFileSource,    {"blk_dir": BLK_DIR}),
    (P2PSource,        {"peer_ip": PEER_IP}),
    (MempoolApiSource, {}),
])
def test_extract_from_sources(src_class, kwargs):
    kwargs["start_height"] = SAMPLE_H
    kwargs["end_height"] = SAMPLE_H
    src = src_class(**kwargs)
    utxos = _collect_utxos(src)

    assert isinstance(utxos, list)
    assert all("tx_id" in u and "type" in u and "value" in u for u in utxos)
    assert all(u["height"] == SAMPLE_H for u in utxos)
    assert len(utxos) > 0
