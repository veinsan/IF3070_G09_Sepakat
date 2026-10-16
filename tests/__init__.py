"""Unit test. Jalankan dari root repo: `python -m unittest discover -s tests -t .`"""

import sys
from pathlib import Path

# kode dijalankan dengan `src/` sebagai root import (DESIGN §10)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
