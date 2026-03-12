import json
import re
from typing import Dict, Any, List, Tuple, cast
from datetime import datetime, timezone


def darken_color(hex_color: str, amount: float = 0.2) -> str:
    """Darken a hex color by a given amount."""
    hex_color = str(hex_color).lstrip('#')
    if len(hex_color) != 6:
        return "#000000"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = int(r * (1 - amount))
    g = int(g * (1 - amount))
    b = int(b * (1 - amount))

    return f"#{r:02x}{g:02x}{b:02x}"


def generate_svg(state: Dict[str, Any]) -> str:
    """Generate the game board SVG from current state."""
    width = 1040
    height = 720

    parts: List[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append(f'  <rect width="{width}" height="{height}" fill="#0d1117" />')
    parts.append(f'  <g font-family="\'Courier New\', monospace">')

    grid = cast(Dict[str, Any], state.get("grid", {}))
    players = cast(Dict[str, Any], state.get("players", {}))

    # Draw Grid
    for row in range(15):
        for col in range(20):
            coord = f"{col},{row}"
            x = 20 + col * 42
            y = 20 + row * 42

            if coord in grid:
                cell_data = cast(Dict[str, Any], grid[coord])
                owner = str(cell_data.get("owner", ""))
                player_data = cast(Dict[str, Any], players.get(owner, {}))
                color = str(player_data.get("color", "#888888"))
                stroke = darken_color(color)
                abbrev = owner[:2].upper()

                parts.append(f'    <rect x="{x}" y="{y}" width="40" height="40" fill="{color}" stroke="{stroke}" stroke-width="1" rx="4" ry="4" />')
                parts.append(f'    <text x="{x + 20}" y="{y + 25}" fill="#ffffff" font-size="12" text-anchor="middle" font-weight="bold">{abbrev}</text>')
            else:
                parts.append(f'    <rect x="{x}" y="{y}" width="40" height="40" fill="#21262d" stroke="#30363d" stroke-width="1" rx="4" ry="4" />')

    # Leaderboard
    parts.append(f'    <text x="880" y="40" fill="#e6edf3" font-size="16" font-weight="bold">TOP PLAYERS</text>')

    sorted_players: List[Tuple[str, Any]] = sorted(
        players.items(),
        key=lambda item: int(cast(Dict[str, Any], item[1]).get("cell_count", 0)),
        reverse=True
    )[:5]

    ly = 80
    for name, p_any in sorted_players:
        p_dict = cast(Dict[str, Any], p_any)
        color = str(p_dict.get("color", "#888888"))
        count = int(p_dict.get("cell_count", 0))
        display_name = str(name)[:10]
        parts.append(f'    <rect x="880" y="{ly - 12}" width="16" height="16" fill="{color}" rx="2" ry="2"/>')
        parts.append(f'    <text x="904" y="{ly}" fill="#c9d1d9" font-size="14">{display_name}</text>')
        parts.append(f'    <text x="1000" y="{ly}" fill="#8b949e" font-size="14" text-anchor="end">{count}</text>')
        ly += 30

    parts.append(f'    <text x="880" y="{height - 40}" fill="#8b949e" font-size="12">Moves reset daily</text>')

    # Progress bar
    total_cells = len(grid)
    pct = total_cells / 300.0
    bar_width = 840
    fill_width = bar_width * pct
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    parts.append(f'    <rect x="20" y="670" width="{bar_width}" height="6" fill="#21262d" rx="3" ry="3"/>')
    parts.append(f'    <rect x="20" y="670" width="{fill_width}" height="6" fill="#3fb950" rx="3" ry="3"/>')
    parts.append(f'    <text x="20" y="700" fill="#8b949e" font-size="12">Territory claimed: {total_cells}/300 ({int(pct * 100)}%)</text>')
    parts.append(f'    <text x="440" y="700" fill="#8b949e" font-size="12" text-anchor="middle">Board resets monthly</text>')
    parts.append(f'    <text x="860" y="700" fill="#8b949e" font-size="12" text-anchor="end">Last updated: {now_str}</text>')
    parts.append('  </g>')
    parts.append('</svg>')

    return "\n".join(parts)


def generate_markdown_links(state: Dict[str, Any]) -> str:
    """Generate a clickable markdown table for the game grid."""
    grid = cast(Dict[str, Any], state.get("grid", {}))
    md: List[str] = []

    for row in range(15):
        row_cells: List[str] = []
        for col in range(20):
            coord = f"{col},{row}"
            encoded_title = f"CLAIM+{col}%2C{row}"
            link = f"https://github.com/eequaled/eequaled/issues/new?title={encoded_title}&labels=game-move"

            if coord in grid:
                cell_data = cast(Dict[str, Any], grid[coord])
                owner = str(cell_data.get("owner", ""))
                text = owner[:2].upper()
            else:
                text = "\u00b7"

            row_cells.append(f" [{text}]({link}) ")

        row_str = "|" + "|".join(row_cells) + "|"

        if row == 0:
            header = "|" + "|".join([" " for _ in range(20)]) + "|"
            sep = "|" + "|".join(["---" for _ in range(20)]) + "|"
            md.append(header)
            md.append(sep)

        md.append(row_str)

    return "\n".join(md)


def update_readme(state: Dict[str, Any]) -> None:
    """Update the README.md with new game links between markers."""
    links_md = generate_markdown_links(state)

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Replace content between markers
        pattern = r"(<!-- GAME_LINKS_START -->).*?(<!-- GAME_LINKS_END -->)"
        replacement = f"\\1\n\n{links_md}\n\n\\2"
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"Failed to update README: {e}")
