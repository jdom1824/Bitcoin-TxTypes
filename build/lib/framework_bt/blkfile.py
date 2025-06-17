import os
import struct
import multiprocessing
from bitcoin.core import CBlock
from typing import Iterator, Optional  # ← Faltaba esto

MAGIC_BYTES = b"\xf9\xbe\xb4\xd9"
MAGIC_LEN = 4
LENGTH_LEN = 4


def process_blk_file(path, target_hash, found_event, result_queue):
    with open(path, "rb") as f:
        while not found_event.is_set():
            magic = f.read(MAGIC_LEN)
            if not magic:
                break
            if magic != MAGIC_BYTES:
                continue
            raw_len = f.read(LENGTH_LEN)
            if len(raw_len) < 4:
                break
            block_size = struct.unpack("<I", raw_len)[0]
            raw_block = f.read(block_size)
            if len(raw_block) < block_size:
                break

            blk_hash = CBlock.deserialize(raw_block).GetHash().hex()
            if blk_hash == target_hash:
                found_event.set()
                result_queue.put({
                    "path": path,
                    "hash": blk_hash,
                    "raw": raw_block,
                })
                break


def find_block_parallel(blk_dir, target_hash):
    blk_files = sorted(
        os.path.join(blk_dir, f)
        for f in os.listdir(blk_dir)
        if f.startswith("blk") and f.endswith(".dat")
    )

    manager = multiprocessing.Manager()
    found_event = manager.Event()
    result_queue = manager.Queue()

    processes = []
    for path in blk_files:
        p = multiprocessing.Process(
            target=process_blk_file,
            args=(path, target_hash, found_event, result_queue)
        )
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    if not result_queue.empty():
        return result_queue.get()
    else:
        return None


def _process_file_for_range(args):
    path, height_offset, start_height, end_height = args
    results = []
    local_count = 0
    global_height = height_offset

    with open(path, "rb") as f:
        while True:
            magic = f.read(MAGIC_LEN)
            if not magic:
                break
            if magic != MAGIC_BYTES:
                continue
            raw_len = f.read(LENGTH_LEN)
            if len(raw_len) < 4:
                break
            block_size = struct.unpack("<I", raw_len)[0]
            raw_block = f.read(block_size)
            if len(raw_block) < block_size:
                break

            if global_height < start_height:
                local_count += 1
                global_height += 1
                continue
            if global_height > end_height:
                break

            blk_hash = CBlock.deserialize(raw_block).GetHash()

            results.append({
                "height": global_height,
                "hash": blk_hash.hex(),
                "raw": raw_block,
            })

            local_count += 1
            global_height += 1

    return results


class ParallelBlkFileSource:
    def __init__(
        self,
        blk_dir: str,
        start_height: Optional[int] = 0,
        end_height: Optional[int] = None,
        processes: int = 4,
    ):
        self.blk_dir = blk_dir
        self.start_height = start_height or 0
        self.end_height = end_height or 0xFFFFFFFF
        self.processes = processes

    def __iter__(self) -> Iterator[dict]:
        blk_files = sorted(
            f for f in os.listdir(self.blk_dir)
            if f.startswith("blk") and f.endswith(".dat")
        )
        full_paths = [os.path.join(self.blk_dir, f) for f in blk_files]

        # Estimar: ~3000 bloques por archivo (ajustable)
        estimated_offsets = {path: i * 3000 for i, path in enumerate(full_paths)}

        args = [
            (path, estimated_offsets[path], self.start_height, self.end_height)
            for path in full_paths
        ]

        with multiprocessing.Pool(processes=self.processes) as pool:
            for result in pool.imap_unordered(_process_file_for_range, args):
                for blk in result:
                    yield blk  # ← Le faltaba cerrar el paréntesis aquí
