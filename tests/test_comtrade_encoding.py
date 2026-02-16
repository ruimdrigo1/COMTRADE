import tempfile
import unittest
from pathlib import Path

from src.comtrade_encoding import decode_cfg_bytes, write_cfg_as_utf8


class TestComtradeEncoding(unittest.TestCase):
    def test_decode_cp1252_bytes(self):
        text = "ESTAÇAO,ID,1999"
        cfg_bytes = text.encode("cp1252")

        decoded, used = decode_cfg_bytes(cfg_bytes, extra_candidates=["cp1252"])

        self.assertEqual(decoded, text)
        self.assertEqual(used.lower(), "cp1252")

    def test_write_utf8_cfg_from_latin1(self):
        text = "LINHA Ç,2A,50"
        cfg_bytes = text.encode("latin-1")

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "sample.cfg"
            used = write_cfg_as_utf8(cfg_bytes, str(cfg_path), extra_candidates=["latin-1"])

            self.assertEqual(used.lower(), "latin-1")
            written = cfg_path.read_text(encoding="utf-8")
            self.assertEqual(written, text)


if __name__ == "__main__":
    unittest.main()
