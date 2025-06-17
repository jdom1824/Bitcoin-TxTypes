# cli.py
# ======
# Installed as `bt-extract` via pyproject.toml.
#
# Available sources:
#   • blk*.dat files         (--blk-dir)   [sequential or parallel reading]
#   • bitcoind via RPC       (--rpc  + --rpc-url=…)
#   • Direct P2P             (--p2p  [--peer-ip=…])
#   • mempool.space API      (--mempool)

from __future__ import annotations
import click, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

from .rpcsource     import RpcSource
from .p2psource     import P2PSource
from .mempoolsource import MempoolApiSource
from .blkfile       import BlkFileSource, ParallelBlkFileSource
from .classifier    import StandardClassifier
from .extractor     import extract


@click.command()
# ───────────── Sources ─────────────
@click.option("--blk-dir", type=click.Path(exists=True, file_okay=False),
              help="Directory containing blk*.dat files")
@click.option("--rpc", is_flag=True,
              help="Use bitcoind node via RPC")
@click.option("--rpc-url", type=str,
              help="Full RPC URL (e.g. http://user:pass@127.0.0.1:8332)")
@click.option("--p2p", is_flag=True,
              help="Download blocks via P2P (seeds + Bitnodes)")
@click.option("--peer-ip", type=str,
              help="Fixed IP of a P2P node (optional)")
@click.option("--mempool", is_flag=True,
              help="Download blocks via HTTPS from mempool.space")
# ───────────── Range ───────────────
@click.option("--start-height", type=int, required=True,
              help="Start block height (inclusive)")
@click.option("--end-height", type=int, required=True,
              help="End block height (inclusive)")
# ───────────── Performance ─────────
@click.option("--parallel", is_flag=True,
              help="Enable parallel reading of blk*.dat files")
@click.option("--processes", type=int, default=4, show_default=True,
              help="Number of processes for deserialization")
# ───────────── Output ──────────────
@click.option("--output", type=str, default="utxos", show_default=True,
              help="Prefix for output Parquet files")
@click.option("--chunk-size", type=int, default=100_000, show_default=True,
              help="Number of UTXOs per Parquet file")
def main(blk_dir, rpc, rpc_url, p2p, peer_ip, mempool,
         start_height, end_height,
         parallel, processes,
         output, chunk_size):
    """Extracts and classifies UTXOs, saving them in Parquet chunks."""

    # ── Ensure only one source is selected ─────────────────────────────
    chosen = sum(map(bool, [blk_dir, rpc, p2p, mempool]))
    if chosen != 1:
        raise click.UsageError("You must select **one** source: "
                               "--blk-dir | --rpc | --p2p | --mempool")

    # ── Construct appropriate source ───────────────────────────────────
    if blk_dir:
        source = (ParallelBlkFileSource if parallel else BlkFileSource)(
            blk_dir, start_height, end_height,
            **({"processes": processes} if parallel else {}))

    elif rpc:
        if not rpc_url:
            raise click.UsageError("--rpc requires --rpc-url.")
        source = RpcSource(rpc_url, start_height, end_height)

    elif p2p:
        source = P2PSource(start_height, end_height, peer_ip=peer_ip)

    else:  # mempool
        source = MempoolApiSource(start_height, end_height)

    # ── Extraction + Writing to Parquet ────────────────────────────────
    classifier = StandardClassifier()
    buffer = []
    chunk_idx = 1
    total = 0

    for utxo in extract(source, classifier, processes=processes,
                        start_height=start_height, end_height=end_height):
        buffer.append(utxo)
        if len(buffer) >= chunk_size:
            _write_chunk(buffer, output, chunk_idx)
            total += len(buffer)
            buffer.clear()
            chunk_idx += 1

    if buffer:
        _write_chunk(buffer, output, chunk_idx)
        total += len(buffer)

    click.echo(f"[✓] {total} UTXOs saved to {chunk_idx} file(s)")


# ───────── Helper to write Parquet files ─────────
def _write_chunk(buf, prefix, idx):
    pq.write_table(pa.Table.from_pandas(pd.DataFrame(buf)),
                   f"{prefix}_{idx:04d}.parquet")
    click.echo(f"[→] {len(buf)} UTXOs → {prefix}_{idx:04d}.parquet")


if __name__ == "__main__":
    main()
