"""
cli.py
======
Instalado como `bt-extract` mediante pyproject.toml.

Fuentes disponibles:
  • Archivos blk*.dat  (--blk-dir)   [lectura secuencial o paralela]
  • RPC bitcoind       (--rpc  + --rpc-url=…)
  • P2P directo        (--p2p  [--peer-ip=…])
  • API mempool.space  (--mempool)
"""

from __future__ import annotations
import click, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

from .rpcsource     import RpcSource
from .p2psource     import P2PSource
from .mempoolsource import MempoolApiSource            # ← NUEVO
from .blkfile       import BlkFileSource, ParallelBlkFileSource
from .classifier    import StandardClassifier
from .extractor     import extract


@click.command()
# ───────────── fuentes ─────────────
@click.option("--blk-dir", type=click.Path(exists=True, file_okay=False),
              help="Directorio con archivos blk*.dat")
@click.option("--rpc", is_flag=True,
              help="Usar nodo bitcoind vía RPC")
@click.option("--rpc-url", type=str,
              help="URL RPC (ej: http://user:pass@127.0.0.1:8332)")
@click.option("--p2p", is_flag=True,
              help="Descargar por P2P (seeds + Bitnodes)")
@click.option("--peer-ip", type=str,
              help="IP fija de un nodo P2P (opcional)")
@click.option("--mempool", is_flag=True,
              help="Descargar siempre por HTTPS desde mempool.space")
# ───────────── rango ───────────────
@click.option("--start-height", type=int, required=True,
              help="Altura inicial")
@click.option("--end-height", type=int, required=True,
              help="Altura final (incl.)")
# ───────────── rendimiento ─────────
@click.option("--parallel", is_flag=True,
              help="Lectura paralela de blk*.dat")
@click.option("--processes", type=int, default=4, show_default=True,
              help="Procesos de deserialización")
# ───────────── salida ──────────────
@click.option("--output", type=str, default="utxos", show_default=True,
              help="Prefijo de archivos Parquet")
@click.option("--chunk-size", type=int, default=100_000, show_default=True,
              help="UTXOs por archivo Parquet")
def main(blk_dir, rpc, rpc_url, p2p, peer_ip, mempool,
         start_height, end_height,
         parallel, processes,
         output, chunk_size):
    """Extrae UTXO y los guarda en fragmentos Parquet."""

    # ── validar elección única ──────────────────
    chosen = sum(map(bool, [blk_dir, rpc, p2p, mempool]))
    if chosen != 1:
        raise click.UsageError("Seleccione **una** fuente: "
                               "--blk-dir | --rpc | --p2p | --mempool")

    # ── construir fuente ────────────────────────
    if blk_dir:
        source = (ParallelBlkFileSource if parallel else BlkFileSource)(
            blk_dir, start_height, end_height,
            **({"processes": processes} if parallel else {}))

    elif rpc:
        if not rpc_url:
            raise click.UsageError("--rpc requiere --rpc-url.")
        source = RpcSource(rpc_url, start_height, end_height)

    elif p2p:
        source = P2PSource(start_height, end_height, peer_ip=peer_ip)

    else:  # mempool
        source = MempoolApiSource(start_height, end_height)

    # ── extracción → Parquet ─────────────────────
    classifier, buffer, chunk_idx, total = StandardClassifier(), [], 1, 0

    for utxo in extract(source, classifier, processes=processes,
                        start_height=start_height, end_height=end_height):
        buffer.append(utxo)
        if len(buffer) >= chunk_size:
            _write_chunk(buffer, output, chunk_idx)
            total += len(buffer); buffer.clear(); chunk_idx += 1

    if buffer:
        _write_chunk(buffer, output, chunk_idx)
        total += len(buffer)

    click.echo(f"[✓] {total} UTXO guardados en {chunk_idx} archivo(s)")


# ───────── helper Parquet ──────────
def _write_chunk(buf, prefix, idx):
    pq.write_table(pa.Table.from_pandas(pd.DataFrame(buf)),
                   f"{prefix}_{idx:04d}.parquet")
    click.echo(f"[→] {len(buf)} UTXO → {prefix}_{idx:04d}.parquet")


if __name__ == "__main__":
    main()
