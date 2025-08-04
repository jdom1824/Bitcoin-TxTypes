class StandardClassifier:
    TYPES = {
        "P2PKH": ("76a914", "88ac"),
        "P2SH":  ("a914",  "87"),
        "P2WPKH": ("0014", 44),   # 0x00 OP_DATA_20
        "P2WSH":  ("0020", 68),   # 0x00 OP_DATA_32
        "P2TR":   ("5120", 68),   # OP_1 OP_DATA_32 (Taproot)
    }

    def classify(self, script_hex: str, *, coinbase: bool = False) -> str:
        if not script_hex:
            return "UNKNOWN"

        s = script_hex.lower()

        # 1. Casos triviales
        if coinbase:
            return "COINBASE"
        if s.startswith("6a"):
            return "OP_RETURN"

        # 2. P2PKH  &  P2SH
        if s.startswith(self.TYPES["P2PKH"][0]) and s.endswith(self.TYPES["P2PKH"][1]):
            return "P2PKH"
        if s.startswith(self.TYPES["P2SH"][0])  and s.endswith(self.TYPES["P2SH"][1]):
            return "P2SH"

        # 3. Witness v0
        if s.startswith(self.TYPES["P2WPKH"][0]) and len(s) == self.TYPES["P2WPKH"][1]:
            return "P2WPKH"
        if s.startswith(self.TYPES["P2WSH"][0])  and len(s) == self.TYPES["P2WSH"][1]:
            return "P2WSH"

        # 4. Taproot (witness v1)
        if s.startswith(self.TYPES["P2TR"][0])   and len(s) == self.TYPES["P2TR"][1]:
            return "P2TR"

        # 5. P2PK  (según estándar Bitcoin Core)
        #    a) 33-byte compressed pubkey  →  0x21 + 33 B + 0xac  → 68 hex chars
        #    b) 65-byte uncompressed      →  0x41 + 65 B + 0xac  → 134 hex chars
        if s.endswith("ac"):
            if len(s) == 68  and s[:2] == "21" and s[2:4] in ("02", "03"):
                return "P2PK"
            if len(s) == 134 and s[:2] == "41" and s[2:4] == "04":
                return "P2PK"

        # 6. Si contiene algo pero no coincide con ningún patrón estándar
        if len(s) >= 4:
            return "OTHER"
        return "UNKNOWN"
