"""
classifier.py
=============
Simple classifier of scriptPubKey ➜ output type.
"""

class StandardClassifier:
    TYPES = {
        "P2PKH": ("76a914", "88ac"),
        "P2SH": ("a914", "87"),
        "P2WPKH": ("0014", 44),  # 20 bytes = 40 hex + "0014" (4 chars)
        "P2WSH": ("0020", 68),   # 32 bytes = 64 hex + "0020" (4 chars)
    }

    def classify(self, script_hex: str, *, coinbase: bool = False) -> str:
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

        return "OTHER"
