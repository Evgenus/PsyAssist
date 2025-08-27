#!/usr/bin/env python3
"""
Run script for PsyAssist AI.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from psyassist.config.settings import settings


def main():
    """Run the PsyAssist AI server."""
    print("🚀 Starting PsyAssist AI...")
    print(f"📊 API Host: {settings.api_host}")
    print(f"🔌 API Port: {settings.api_port}")
    print(f"🌐 API Prefix: {settings.api_prefix}")
    print(f"🔧 Debug Mode: {settings.debug}")
    print()
    
    # Run the server
    uvicorn.run(
        "psyassist.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )


if __name__ == "__main__":
    main()
