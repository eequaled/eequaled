import os
import sys
import json
from typing import Dict, Any
from datetime import datetime, timezone

# Allow importing shared.py from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import generate_svg, update_readme  # type: ignore


def main() -> None:
    state_path: str = "assets/game-state.json"
    board_path: str = "assets/game-board.svg"

    # Generate empty state
    state: Dict[str, Any] = {
        "grid": {},
        "players": {},
        "meta": {
            "grid_width": 20,
            "grid_height": 15,
            "max_moves_per_day": 3,
            "last_reset": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_moves": 0
        }
    }

    os.makedirs("assets", exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # Generate SVG board
    svg: str = generate_svg(state)
    with open(board_path, "w", encoding="utf-8") as f:
        f.write(svg)

    # Update README links
    update_readme(state)
    print("Game reset successfully.")


if __name__ == "__main__":
    main()
