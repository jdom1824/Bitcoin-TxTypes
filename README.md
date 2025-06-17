# Framework-Bitcoin-TxTypes

A lightweight Python framework for extracting and classifying Bitcoin transaction outputs (UTXOs) by type — directly from the Bitcoin blockchain.

✅ Works with:
- `.blk` raw block files from Bitcoin Core
- Bitcoin Core via RPC interface
- P2P download using block hashes and public nodes
- Mempool.space HTTP API

### 🎯 Purpose

Analyze Bitcoin transaction output types (P2PKH, P2SH, P2WPKH, etc.) across the blockchain — ideal for research, statistics, protocol studies, or forensic auditing.

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

### 2️⃣ Local blk\*.dat (fastest & parallel)

```bash
bt-extract   --blk-dir /path/to/blocks   --parallel   --processes 8   --start-height 100000   --end-height   100000   --output utxos
```

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
bt-view --prefix utxos --head 15
```

Lists files, previews rows, and shows a summary (row count, total BTC, distribution by type, file size).

---

## ✅ Tests

```bash
pytest
```

Includes block equivalence tests (RPC vs HTTPS) and parsing validation.

---

## 📄 License

MIT License. Free for academic and commercial use.
