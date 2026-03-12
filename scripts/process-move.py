import os
import sys
import json
import hashlib
import colorsys
from typing import Dict, Any, Optional, cast
from datetime import datetime, timezone

# Allow importing shared.py from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import generate_svg, update_readme  # type: ignore


def main() -> None:
    move_player_raw: Optional[str] = os.environ.get("MOVE_PLAYER")
    move_coords_raw: Optional[str] = os.environ.get("MOVE_COORDS")

    if move_player_raw is None:
        write_result("Error: Missing player.")
        return
    if move_coords_raw is None:
        write_result("Error: Missing coordinates.")
        return

    # Now narrowed to str by Pyright
    move_player: str = move_player_raw
    move_coords: str = move_coords_raw

    try:
        col_str, row_str = move_coords.split(",")
        col: int = int(col_str.strip())
        row: int = int(row_str.strip())
    except Exception:
        write_result("Error: Invalid coordinate format.")
        return

    if col < 0 or col >= 20 or row < 0 or row >= 15:
        write_result("Error: Coordinates out of bounds (0-19, 0-14).")
        return

    state_path: str = "assets/game-state.json"
    board_path: str = "assets/game-board.svg"

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state: Dict[str, Any] = json.load(f)
    except FileNotFoundError:
        write_result("Error: Game state not found. Has it been initialized?")
        return

    grid = cast(Dict[str, Any], state.setdefault("grid", {}))
    players = cast(Dict[str, Any], state.setdefault("players", {}))
    meta = cast(Dict[str, Any], state.setdefault("meta", {}))

    today: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_full: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    player_any: Any = players.get(move_player)

    # 1. Rate Limit
    if player_any is not None:
        player_check = cast(Dict[str, Any], player_any)
        if player_check.get("last_move_date") == today:
            moves_today: int = int(player_check.get("moves_today", 0))
            max_moves: int = int(meta.get("max_moves_per_day", 3))
            if moves_today >= max_moves:
                write_result(f"Rate limit exceeded. Max {max_moves} moves/day. Try tomorrow!")
                return

    # 2. Check if cell is already claimed
    coord_key: str = f"{col},{row}"
    if coord_key in grid:
        cell_data = cast(Dict[str, Any], grid[coord_key])
        owner: str = str(cell_data.get("owner", ""))
        write_result(f"Cell {coord_key} is already owned by @{owner}.")
        return

    # 3. Adjacency check (only for players who already have territory)
    if player_any is not None:
        p_adj = cast(Dict[str, Any], player_any)
        if int(p_adj.get("cell_count", 0)) > 0:
            adjacent = [
                f"{col-1},{row}",
                f"{col+1},{row}",
                f"{col},{row-1}",
                f"{col},{row+1}"
            ]
            has_adj: bool = any(
                adj in grid and cast(Dict[str, Any], grid[adj]).get("owner") == move_player
                for adj in adjacent
            )
            if not has_adj:
                write_result("Invalid move. You must expand to an adjacent cell.")
                return

    # All checks pass — apply the move
    grid[coord_key] = {
        "owner": move_player,
        "claimed_at": now_full
    }

    player: Dict[str, Any]
    if player_any is None:
        # New player: generate a unique color from their username
        hue: int = int(hashlib.md5(move_player.encode("utf-8")).hexdigest(), 16) % 360
        r_f, g_f, b_f = colorsys.hls_to_rgb(hue / 360.0, 0.55, 0.70)
        color_hex: str = f"#{int(r_f * 255):02x}{int(g_f * 255):02x}{int(b_f * 255):02x}"

        player = {
            "color": color_hex,
            "cell_count": 0,
            "moves_today": 0,
            "last_move_date": today
        }
        players[move_player] = player
    else:
        player = cast(Dict[str, Any], player_any)

    # Update player stats
    player["cell_count"] = int(player.get("cell_count", 0)) + 1
    if str(player.get("last_move_date")) == today:
        player["moves_today"] = int(player.get("moves_today", 0)) + 1
    else:
        player["last_move_date"] = today
        player["moves_today"] = 1

    meta["total_moves"] = int(meta.get("total_moves", 0)) + 1

    # Save state
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # Generate SVG board
    svg: str = generate_svg(state)
    with open(board_path, "w", encoding="utf-8") as f:
        f.write(svg)

    # Update README links
    update_readme(state)

    write_result(f"Success! @{move_player} claimed {coord_key}.")


def write_result(msg: str) -> None:
    """Write the result message to stdout and GITHUB_ENV."""
    print(msg)
    env_file: Optional[str] = os.environ.get("GITHUB_ENV")
    if env_file:
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"MOVE_RESULT={msg}\n")


if __name__ == "__main__":
    main()
