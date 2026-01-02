"""Project configuration values shared across scripts."""

PALETTE = [
    "#EDDCCF",  # beige
    "#C9D6C5",  # soft green
    "#EDEFF1",  # light gray
    "#F7EDE6",  # very light peach
    "#CBB0A0",  # light brown
]


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#" + "".join(f"{int(max(0,min(255,v))):02x}" for v in rgb)


def generate_shades(base_colors, shades_per_color=3):
    """Generate related shades for each base color.

    For each base color we generate shades by slightly darkening and lightening the color.
    Returns a flat list of hex color strings.
    """
    t_values = []
    # create factors around 0: negative for darker, positive for lighter
    if shades_per_color == 1:
        t_values = [0.0]
    else:
        # symmetric around 0, include 0
        half = (shades_per_color - 1) // 2
        # spacing step
        step = 0.12
        # build list like [-0.12, 0.0, 0.12] for 3 shades
        t_values = [(-half + i) * step for i in range(shades_per_color)]

    out = []
    for c in base_colors:
        r, g, b = _hex_to_rgb(c)
        for t in t_values:
            if t >= 0:
                nr = int(r + (255 - r) * t)
                ng = int(g + (255 - g) * t)
                nb = int(b + (255 - b) * t)
            else:
                nr = int(r * (1 + t))
                ng = int(g * (1 + t))
                nb = int(b * (1 + t))
            out.append(_rgb_to_hex((nr, ng, nb)))
    # return unique while preserving order
    seen = set()
    uniq = []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq

# Expanded palette derived from PALETTE to reduce color repetition
EXPANDED_PALETTE = generate_shades(PALETTE, shades_per_color=4)
