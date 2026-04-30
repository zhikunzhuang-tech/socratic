"""python -m socratic"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from socratic.cli import main
main()
