from framework_bt.blkfile import BlkFileSource, ParallelBlkFileSource
import os


def test_blkfile_equivalence():
    blk_dir = "/media/jdom-sas/node/Bitcoin/blocks"
    assert os.path.isdir(blk_dir), f"Directory not found: {blk_dir}"

    start_height = 700000
    end_height = 700020  # pequeño rango para pruebas

    # Modo secuencial
    seq_source = BlkFileSource(blk_dir, start_height=start_height, end_height=end_height)
    seq_blocks = {blk["height"]: blk["hash"] for blk in seq_source}

    # Modo paralelo
    par_source = ParallelBlkFileSource(blk_dir, start_height=start_height, end_height=end_height, processes=2)
    par_blocks = {blk["height"]: blk["hash"] for blk in par_source}

    assert seq_blocks.keys() == par_blocks.keys(), "Las alturas no coinciden"
    for height in seq_blocks:
        assert seq_blocks[height] == par_blocks[height], f"Hash distinto en altura {height}"
