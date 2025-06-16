"""
classifier.py
=============
Clasificador sencillo de scriptPubKey ➜ tipo de salida.
"""
class StandardClassifier:
    TYPES = {
        "P2PKH": ("76a914", "88ac"),
        "P2SH": ("a914", "87"),
        "P2WPKH": ("0014", 22 * 2),  # 22 bytes * 2 hex chars
        "P2WSH": ("0020", 34 * 2),   # 34 bytes
    }

    def classify(self, script_hex: str, *, coinbase: bool = False) -> str:
        if coinbase:
            return "COINBASE"
        s = script_hex.lower()

        if s.startswith("6a"):
            return "OP_RETURN"
        if s.startswith(self.TYPES["P2PKH"][0]) and s.endswith(self.TYPES["P2PKH"][1]):
            return "P2PKH"
        if s.startswith(self.TYPES["P2SH"][0]) and s.endswith(self.TYPES["P2SH"][1]):
            return "P2SH"
        if s.startswith(self.TYPES["P2WPKH"][0]) and len(s) == 4 + self.TYPES["P2WPKH"][1]:
            return "P2WPKH"
        if s.startswith(self.TYPES["P2WSH"][0]) and len(s) == 4 + self.TYPES["P2WSH"][1]:
            return "P2WSH"
        return "OTHER"
