# Framework-Bitcoin-TxTypes

A lightweight Python framework for extracting and classifying Bitcoin transaction outputs (UTXOs) by type — directly from the Bitcoin blockchain.

✅ Works with:
- `.blk` raw block files from Bitcoin Core
- Bitcoin Core via RPC interface
- P2P download using block hashes and public nodes
- Mempool.space HTTP API

### 🎯 Purpose

Analyze Bitcoin transaction output types (P2PKH, P2SH, P2WPKH, etc.) across the blockchain — ideal for research, statistics, and, protocol studies.
![Unlock Chain Diagram](unlock-chain.png)

---

## ✅ Features

- Python 3.10+ compatible  
- No heavy dependencies like BlockSci  
- Outputs clean `.parquet` files for easy processing  
- CLI tools: `bt-extract` and `bt-view`  
- Four block sources:  
  1. Local blk *.dat files  
  2. Bitcoin Core RPC  
  3. P2P protocol  
  4. HTTPS API (mempool.space)  
- Multiprocessing for high performance  

---

## 📦 Installation

```bash
git clone https://github.com/jdom1824/Bitcoin-TxTypes.git
cd Framework-Bitcoin-TxTypes
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

This installs the CLI scripts `bt-extract` and `bt-view` directly in your environment.

---

## 🚀 Usage

### 1️⃣ RPC Mode

```bash
bt-extract   --rpc   --rpc-url "http://user:password@127.0.0.1:8332"   --start-height 100000   --end-height   100000   --output utxos
```

---

### 2️⃣ From blk*.dat files (fastest & scalable)

**Ideal for large-scale processing**: reads local Bitcoin Core block files with **parallel decoding**.

#### 🧭 Step 1: Generate the block index (sequential)

Before using parallel processing, the tool builds an index file `.blkindex.json` that maps block heights to their location (file + offset). This is done automatically the first time you run `bt-extract` **without `--parallel`**:

```bash
bt-extract   --blk-dir /path/to/blocks   --start-height 0   --end-height 1000   --output utxos
```

This will:

- Scan all `blk*.dat` files.
- Identify every block.
- Create `.blkindex.json` in the same directory.
- Extract UTXOs in a single process.

#### ⚡ Step 2: Run in parallel mode (faster)

Once the index exists, you can use `--parallel` and `--processes` to decode multiple files concurrently:

```bash
bt-extract   --blk-dir /path/to/blocks   --parallel   --processes 8   --start-height 100000   --end-height   200000   --output utxos
```

Internally, the tool:

- Reads the `.blkindex.json` to get exact file/offsets per height.
- Distributes blocks across worker processes.
- Each process deserializes blocks and extracts UTXOs concurrently.

#### ℹ️ Notes

- If the index does **not** exist, it will be created automatically — but only when **not using** `--parallel`.
- The default height estimation (~3000 blocks per `blk*.dat`) is only a fallback; the index provides accurate mapping.

---
#### ⚠️ Recommended for full blockchain extraction

To avoid memory saturation, we **recommend splitting extraction in batches** using a Bash script that processes every 10.000 blocks:

```bash
#!/bin/bash
START=774999
END=870400
STEP=1000 # recommended for 16GB RAM
OUTDIR="utxos_blk"
BLKDIR="/media/jdom-sas/node/Bitcoin/blocks"
PROCESSES=10  # Número de procesos a usar

mkdir -p "$OUTDIR"

for (( HEIGHT=$START; HEIGHT<=$END; HEIGHT+=$STEP ))
do
    FROM=$HEIGHT
    TO=$(( HEIGHT + STEP - 1 ))
    if [ $TO -gt $END ]; then
        TO=$END
    fi

    echo "Processing blocks $FROM a $TO..."

    bt-extract \
      --blk-dir "$BLKDIR" \
      --start-height "$FROM" \
      --end-height "$TO" \
      --output "$OUTDIR/utxos_${FROM}_${TO}" \
      --processes "$PROCESSES"
done
```

This method guarantees stable RAM usage and allows you to resume or parallelize work more easily.

---

### 3️⃣ P2P Mode

```bash
bt-extract   --p2p   --start-height 100000   --end-height   100000   --output utxos
```

Use a fixed peer if desired:

```bash
bt-extract   --p2p --peer-ip 65.109.158.58   --start-height 100000   --end-height   100000   --output utxos
```

### 4️⃣ HTTPS API Mode (mempool.space)

```bash
bt-extract   --mempool   --start-height 800010   --end-height   800010   --output utxos_http
```

---

## 🔧 Performance Options

- `--parallel`: enable multiprocessing for scanning blk *.dat  
- `--processes N`: number of worker processes (default: 4)  

---

## 🧪 Output

Generates Parquet chunks:

```
utxos_0001.parquet
utxos_0002.parquet
...
```

Columns:

- **height**: block height  
- **tx_id**: transaction ID (hex)  
- **vout**: output index  
- **value**: satoshis  
- **type**: script classification  

Load in Python:

```python
import pandas as pd
df = pd.read_parquet("utxos_0001.parquet")
print(df.head())
```

---

## 👀 Inspect with `bt-view`

```bash
bt-view --prefix '*' --head 15
```

Lists files, previews rows, and shows a summary (row count, total BTC, distribution by type, file size).

---

## ✅ Tests

This project includes the following pytest suites:

- **`tests/test_rpc_source.py`**  
  Verifies `RpcSource` returns valid blocks and transaction lists.

- **`tests/test_blkfile.py`**  
  Checks `BlkFileSource` and `ParallelBlkFileSource` correctly scan block files at height 0.

- **`tests/test_blkfile_equivalence.py`**  
  Ensures serial vs parallel block file sources produce identical blocks.

- **`tests/test_http_vs_rpc.py`**  
  Confirms that blocks fetched via RPC and via the mempool.space HTTP API have matching hashes.

### Running Tests

To run all tests:

```bash
pytest -v
```

To run specific suites:

```bash
pytest tests/test_rpc_source.py tests/test_blkfile.py -v
pytest tests/test_blkfile_equivalence.py tests/test_http_vs_rpc.py -v
```

---

## 📄 License

MIT License. Free for academic and commercial use.
