"""Launch the Chainlit UI without relying on chainlit.exe being on PATH."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> int:
    if importlib.util.find_spec("chainlit") is None:
        print("Chainlit is not installed in this Python environment.")
        print("Install optional UI dependencies first:")
        print("  python -m pip install -r requirements-optional.txt")
        return 1

    app_root = Path(tempfile.gettempdir()) / "ecombot_Capstone_GoogleADK_Chainlit" / "chainlit_runtime"
    app_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("CHAINLIT_APP_ROOT", str(app_root))

    if "--check" in sys.argv:
        print("Chainlit is installed.")
        print(f"Chainlit runtime folder: {app_root}")
        return 0

    command = [sys.executable, "-m", "chainlit", "run", "src/ui/app.py", "-w"]
    return subprocess.call(command, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
