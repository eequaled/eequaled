import os
import json
import urllib.request
import urllib.error
import math
from typing import Dict, Any, List, Tuple

def get_language_stats(token: str, username: str) -> List[Tuple[str, float, str]]:
    """Fetch top languages used by the user across public repositories."""
    query = """
    query {
      user(login: "%s") {
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
          nodes {
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
      }
    }
    """ % username

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Profile-Builder"
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching language stats: {e}")
        # Fallback payload for testing
        return [
            ("Go", 43.24, "#00ADD8"),
            ("TypeScript", 41.28, "#3178c6"),
            ("Java", 11.44, "#b07219"),
            ("JavaScript", 1.81, "#f1e05a"),
            ("CSS", 1.29, "#563d7c"),
            ("PowerShell", 0.42, "#012456"),
            ("Python", 0.38, "#3572A5"),
            ("HTML", 0.13, "#e34c26")
        ]

    langs: Dict[str, Dict[str, Any]] = {}
    total_size = 0

    try:
        repos = data["data"]["user"]["repositories"]["nodes"]
        for repo in repos:
            if not repo or not repo.get("languages") or not repo["languages"].get("edges"):
                continue
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                color = edge["node"]["color"] or "#cccccc"
                size = edge["size"]
                
                if name not in langs:
                    langs[name] = {"color": color, "size": 0}
                langs[name]["size"] += size
                total_size += size
                
        # Calculate percentages
        lang_list = []
        for name, info in langs.items():
            pct = (info["size"] / total_size) * 100
            lang_list.append((name, pct, info["color"]))
            
        # Sort by percentage descending
        lang_list.sort(key=lambda x: x[1], reverse=True)
        return lang_list[:8] # Top 8 languages
    except Exception as e:
        print(f"Error parsing language stats: {e}")
        return []

def polar_to_cartesian(cx: float, cy: float, radius: float, angle_in_degrees: float) -> Tuple[float, float]:
    angle_in_radians = math.radians(angle_in_degrees - 90)
    return (
        cx + (radius * math.cos(angle_in_radians)),
        cy + (radius * math.sin(angle_in_radians))
    )

def describe_arc(x: float, y: float, radius: float, start_angle: float, end_angle: float) -> str:
    start = polar_to_cartesian(x, y, radius, end_angle)
    end = polar_to_cartesian(x, y, radius, start_angle)
    large_arc_flag = "0" if end_angle - start_angle <= 180 else "1"
    return f"M {start[0]} {start[1]} A {radius} {radius} 0 {large_arc_flag} 0 {end[0]} {end[1]}"

def generate_svg(langs: List[Tuple[str, float, str]]) -> str:
    """Generate the unified SVG containing About Me and Language Stats."""
    
    # 1. Start SVG Container (840x340 to fit both panels with a nice gap)
    svg = [
        '<svg width="840" height="340" viewBox="0 0 840 340" fill="none" xmlns="http://www.w3.org/2000/svg">',
        '  <style>',
        '    .code { font-family: monospace, Courier, "Courier New"; font-size: 13px; font-weight: 500; }',
        '    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 600; fill: #7aa2f7; }',
        '    .lang-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 12px; fill: #c0caf5; }',
        '    @keyframes draw {',
        '      to { stroke-dashoffset: 0; }',
        '    }',
        '    .arc { stroke-linecap: round; animation: draw 1.5s ease-out forwards; }',
        '  </style>'
    ]

    # ==========================================
    # LEFT PANEL: About Me (width: 480)
    # ==========================================
    svg.extend([
        '  <!-- Window Glass Background - Left -->',
        '  <g transform="translate(0, 0)">',
        '    <rect width="480" height="340" rx="12" fill="#1a1b26"/>',
        '    <rect x="0.5" y="0.5" width="479" height="339" rx="11.5" stroke="#414868" stroke-opacity="0.5"/>',
        '    <!-- Titlebar -->',
        '    <circle cx="20" cy="20" r="6" fill="#f7768e"/>',
        '    <circle cx="40" cy="20" r="6" fill="#e0af68"/>',
        '    <circle cx="60" cy="20" r="6" fill="#9ece6a"/>',
        '    <!-- Code Content -->',
        '    <g class="code">',
        '      <text x="25" y="55">',
        '        <tspan fill="#bb9af7" font-weight="bold">type</tspan>',
        '        <tspan fill="#2ac3de"> Student </tspan>',
        '        <tspan fill="#bb9af7" font-weight="bold">struct</tspan>',
        '        <tspan fill="#c0caf5"> {</tspan>',
        '      </text>',
        '      <text x="50" y="75"><tspan fill="#7aa2f7">Name</tspan><tspan fill="#c0caf5" xml:space="preserve">     </tspan><tspan fill="#2ac3de">string</tspan></text>',
        '      <text x="50" y="95"><tspan fill="#7aa2f7">Location</tspan><tspan fill="#c0caf5" xml:space="preserve"> </tspan><tspan fill="#2ac3de">string</tspan></text>',
        '      <text x="50" y="115"><tspan fill="#7aa2f7">Focus</tspan><tspan fill="#c0caf5" xml:space="preserve">    </tspan><tspan fill="#89ddff">[]</tspan><tspan fill="#2ac3de">string</tspan></text>',
        '      <text x="50" y="135"><tspan fill="#7aa2f7">Stack</tspan><tspan fill="#c0caf5" xml:space="preserve">    </tspan><tspan fill="#89ddff">[]</tspan><tspan fill="#2ac3de">string</tspan></text>',
        '      <text x="50" y="155"><tspan fill="#7aa2f7">Status</tspan><tspan fill="#c0caf5" xml:space="preserve">   </tspan><tspan fill="#2ac3de">string</tspan></text>',
        '      <text x="25" y="175" fill="#c0caf5">}</text>',
        '      <text x="25" y="205"><tspan fill="#7aa2f7">me</tspan><tspan fill="#c0caf5" xml:space="preserve"> </tspan><tspan fill="#89ddff">:=</tspan><tspan fill="#c0caf5" xml:space="preserve"> </tspan><tspan fill="#2ac3de">Student</tspan><tspan fill="#c0caf5">{</tspan></text>',
        '      <text x="50" y="225"><tspan fill="#7aa2f7">Name</tspan><tspan fill="#89ddff">:</tspan><tspan fill="#c0caf5" xml:space="preserve">     </tspan><tspan fill="#9ece6a">"Hareth Moussaoui (eequaled)"</tspan><tspan fill="#c0caf5">,</tspan></text>',
        '      <text x="50" y="245"><tspan fill="#7aa2f7">Location</tspan><tspan fill="#89ddff">:</tspan><tspan fill="#c0caf5" xml:space="preserve"> </tspan><tspan fill="#9ece6a">"Algiers, Algeria"</tspan><tspan fill="#c0caf5">,</tspan></text>',
        '      <text x="50" y="265"><tspan fill="#7aa2f7">Focus</tspan><tspan fill="#89ddff">:</tspan><tspan fill="#c0caf5" xml:space="preserve"> </tspan><tspan fill="#89ddff">[]</tspan><tspan fill="#2ac3de">string</tspan><tspan fill="#c0caf5">{</tspan><tspan fill="#9ece6a">"Pipelines"</tspan><tspan fill="#c0caf5">, </tspan><tspan fill="#9ece6a">"Automation"</tspan><tspan fill="#c0caf5">},</tspan></text>',
        '      <text x="50" y="285"><tspan fill="#7aa2f7">Stack</tspan><tspan fill="#89ddff">:</tspan><tspan fill="#c0caf5" xml:space="preserve">  </tspan><tspan fill="#89ddff">[]</tspan><tspan fill="#2ac3de">string</tspan><tspan fill="#c0caf5">{</tspan><tspan fill="#9ece6a">"Go"</tspan><tspan fill="#c0caf5">, </tspan><tspan fill="#9ece6a">"TS"</tspan><tspan fill="#c0caf5">, </tspan><tspan fill="#9ece6a">"Rust"</tspan><tspan fill="#c0caf5">, </tspan><tspan fill="#9ece6a">"Python"</tspan><tspan fill="#c0caf5">},</tspan></text>',
        '      <text x="50" y="305"><tspan fill="#7aa2f7">Status</tspan><tspan fill="#89ddff">:</tspan><tspan fill="#c0caf5" xml:space="preserve"> </tspan><tspan fill="#9ece6a">"p2p meshs are massive"</tspan><tspan fill="#c0caf5">,</tspan></text>',
        '      <text x="25" y="325" fill="#c0caf5">}</text>',
        '    </g>',
        '  </g>'
    ])

    # ==========================================
    # RIGHT PANEL: Language Stats (width: 340)
    # Origin: x=500
    # ==========================================
    svg.extend([
        '  <!-- Language Stats - Right -->',
        '  <g transform="translate(500, 0)">',
        '    <rect width="340" height="340" rx="12" fill="#1a1b26"/>',
        '    <rect x="0.5" y="0.5" width="339" height="339" rx="11.5" stroke="#414868" stroke-opacity="0.5"/>',
        '    <text x="30" y="45" class="title">Most Used Languages</text>'
    ])

    # Donut Chart Settings
    cx, cy = 240, 170
    radius = 65
    stroke_width = 16
    circumference = 2 * math.pi * radius

    current_angle = 0
    legend_y = 75

    for name, pct, color in langs:
        # 1. Add Legend Item
        svg.extend([
            f'    <circle cx="35" cy="{legend_y - 4}" r="4" fill="{color}"/>',
            f'    <text x="45" y="{legend_y}" class="lang-text">{name} {pct:.1f}%</text>'
        ])
        legend_y += 28

        # 2. Add Donut Arc
        angle_sweep = (pct / 100) * 360
        # Prevent 360 sweep from causing rendering bugs in SVG arcs
        if angle_sweep >= 359.9:
            angle_sweep = 359.9 
            
        end_angle = current_angle + angle_sweep
        
        # Gap between arcs for elegance (but only if we have more than 1 lang)
        draw_sweep = angle_sweep - 1.5 if len(langs) > 1 and angle_sweep > 1.5 else angle_sweep
        draw_end = current_angle + draw_sweep
        
        path_d = describe_arc(cx, cy, radius, current_angle, draw_end)
        
        # Calculate dash offset for animation
        arc_length = (draw_sweep / 360) * circumference
        
        svg.append(
            f'    <path d="{path_d}" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
            f'stroke-dasharray="{arc_length} {circumference}" stroke-dashoffset="{arc_length}" class="arc" />'
        )
        
        current_angle = end_angle

    svg.extend([
        '  </g>',
        '</svg>'
    ])

    return "\n".join(svg)


if __name__ == "__main__":
    github_token = os.environ.get("GITHUB_TOKEN", "")
    username = os.environ.get("GITHUB_ACTOR", "eequaled")
    
    # In case no token while testing locally, we'll fall back to dummy data
    langs = get_language_stats(github_token, username)
    print(f"Fetched {len(langs)} languages.")
    
    svg_content = generate_svg(langs)
    
    with open("assets/about-me.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print("Successfully generated assets/about-me.svg")
