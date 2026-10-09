#!/usr/bin/env python3
"""
VaultMind Desktop - A desktop application for semantic search of your knowledge vaults.

Usage:
    python main.py          # Start the application
    python main.py --dev   # Start with debug logging
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    if "--dev" in sys.argv:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    from ui.main_window import main
    main()
