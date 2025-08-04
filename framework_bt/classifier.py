class StandardClassifier:
    TYPES = {
        "P2PKH": ("76a914", "88ac"),
        "P2SH": ("a914", "87"),
        "P2WPKH": ("0014", 44),  # OP_0 <20-byte pubKeyHash> => 22 bytes => 44 hex chars
        "P2WSH": ("0020", 68),   # OP_0 <32-byte scriptHash> => 34 bytes => 68 hex chars
        "P2TR": ("5120", 68),    # OP_1 <32-byte x-only pubKey> => 34 bytes => 68 hex chars
    }

    def classify(self, script_hex: str, *, coinbase: bool = False) -> str:
        if not script_hex:
            return "UNKNOWN"

        s = script_hex.lower()

        if coinbase:
            return "COINBASE"

        if s.startswith("6a"):
            return "OP_RETURN"

        if s.startswith(self.TYPES["P2PKH"][0]) and s.endswith(self.TYPES["P2PKH"][1]):
            return "P2PKH"

        if s.startswith(self.TYPES["P2SH"][0]) and s.endswith(self.TYPES["P2SH"][1]):
            return "P2SH"

        if s.startswith(self.TYPES["P2WPKH"][0]) and len(s) == self.TYPES["P2WPKH"][1]:
            return "P2WPKH"

        if s.startswith(self.TYPES["P2WSH"][0]) and len(s) == self.TYPES["P2WSH"][1]:
            return "P2WSH"

        # P2TR detection (starts with OP_1 <32-byte x-only pubKey>)
        if s.startswith(self.TYPES["P2TR"][0]) and len(s) == self.TYPES["P2TR"][1]:
            return "P2TR"

        # P2PK detection (compressed/uncompressed)
        if s.endswith("ac"):
            if s.startswith("04") and len(s) == 132:  # Uncompressed pubkey (65 bytes) + OP_CHECKSIG
                return "P2PK"
            if s.startswith(("02", "03")) and len(s) == 68:  # Compressed pubkey (33 bytes) + OP_CHECKSIG
                return "P2PK"

        # Si no parece nada reconocible, pero no está vacío → OTHER
        if len(s) >= 4:
            return "OTHER"

        return "UNKNOWN"
