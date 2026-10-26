#!/usr/bin/env python3
"""Re-color the pixel-sprites tiger in six passes, one color principle per pass.

Geometry, animation and shading come from ../pixel-sprites/render.py untouched;
only the palette changes. Output: per-pass sprite strips + walk GIFs + data.js
(palettes and metrics) for index.html.

Run from this folder:  python3 recolor.py
"""
import copy, importlib.util, json, math, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "..", "pixel-sprites")
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

spec = importlib.util.spec_from_file_location("render", os.path.join(SPR, "render.py"))
render = importlib.util.module_from_spec(spec); spec.loader.exec_module(render)


# ---------- OKLab ----------
def enc(x): return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
def dec(x): return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

M1 = np.array([[.4122214708, .5363325363, .0514459929], [.2119034982, .6806995451, .1073969566], [.0883024619, .2817188376, .6299787005]])
M2 = np.array([[.2104542553, .7936177850, -.0040720468], [1.9779984951, -2.4285922050, .4505937099], [.0259040371, .7827717662, -.8086757660]])
M1i, M2i = np.linalg.inv(M1), np.linalg.inv(M2)

def rgb2lab(rgb):
    """(...,3) 0..255 -> (...,3) OKLab"""
    a = np.asarray(rgb, float) / 255
    lin = np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)
    return np.cbrt(lin @ M1.T) @ M2.T

def lab2lin(lab): return ((np.asarray(lab, float) @ M2i.T) ** 3) @ M1i.T
def in_gamut(v): return bool(np.all(v >= -1e-4) and np.all(v <= 1.0001))

def lab2rgb(lab):
    L, a, b = lab; L = min(1.0, max(0.0, L))
    v = lab2lin((L, a, b))
    if not in_gamut(v):                       # lose chroma, keep L and hue
        lo, hi = 0.0, 1.0
        for _ in range(12):
            m = (lo + hi) / 2
            if in_gamut(lab2lin((L, a * m, b * m))): lo = m
            else: hi = m
        v = lab2lin((L, a * lo, b * lo))
    return tuple(int(round(255 * min(1, max(0, enc(max(0, x)))))) for x in v)

def lch(L, C, H): return (L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))
def to_lch(lab): return (lab[0], math.hypot(lab[1], lab[2]), math.degrees(math.atan2(lab[2], lab[1])) % 360)
def hexs(rgb): return "%02x%02x%02x" % tuple(rgb)
def hue_delta(H, target, amt): return max(-amt, min(amt, ((target - H + 540) % 360) - 180))


# ---------- reference: tiger-painting.jpg ----------
def analyse_reference():
    im = np.asarray(Image.open(os.path.join(SPR, "references", "tiger-painting.jpg")).convert("RGB"), float)
    lab = rgb2lab(im)
    L = lab[..., 0]; C = np.hypot(lab[..., 1], lab[..., 2])
    H = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    ground = (H > 55) & (H < 120) & (yy > 340)
    handle = (xx > 655) & (xx < 735) & (yy > 550) & (yy < 620)
    tiger = (yy >= 330) & ((H < 45) | (H > 200)) & (L > .2) & (L < .9) & ~handle
    stripe = tiger & (L < .42)
    fur = tiger & (L >= .42)

    def bins(mask, n=4):
        v = lab[mask]; order = np.argsort(v[:, 0]); v = v[order]
        return [v[i * len(v) // n:(i + 1) * len(v) // n].mean(0) for i in range(n)]

    furL = L[fur]; cut = np.percentile(furL, 70)
    core = fur & (L <= cut); pale = fur & (L > cut)
    eye = lab[704:710, 237:243].reshape(-1, 3).mean(0)
    gnd = np.median(im[ground], axis=0)
    return {
        "ground": tuple(int(v) for v in gnd),
        "fur": bins(core), "belly": bins(pale), "stripe": bins(stripe), "eye": eye,
        "stats": {"fur_L": [float(np.percentile(furL, p)) for p in (5, 50, 95)],
                  "stripe_L": float(L[stripe].mean()), "ground_L": float(L[ground].mean()),
                  "tiger_C": float(C[tiger].mean())},
    }

REF = analyse_reference()
REF_COLORS = np.array([c for k in ("fur", "belly", "stripe") for c in REF[k]] + [REF["eye"]])
GROUND_LAB = rgb2lab(np.array(REF["ground"]))


# ---------- passes ----------
cfg0 = json.load(open(os.path.join(SPR, "characters", "tiger.json")))
cfg0["render"]["stripes"] = True      # opt-in feature added to render.py
for _s in cfg0["shapes"]:             # slightly bolder bands: 1px lines vanish at this size
    if "stripes" in _s: _s["stripes"][1] = min(1.0, _s["stripes"][1] * 1.5)
MATS = ["fur", "belly", "stripe"]

def state_from_palette(pal):
    st = {m: [to_lch(rgb2lab([int(pal[f"{m}{i}"][j:j + 2], 16) for j in (0, 2, 4)])) for i in range(4)] for m in MATS}
    st["eye"] = to_lch(rgb2lab([int(pal["eye"][j:j + 2], 16) for j in (0, 2, 4)]))
    st["outline"] = to_lch(rgb2lab([int(pal["outline"][j:j + 2], 16) for j in (0, 2, 4)]))
    return st

def palette_from_state(st):
    pal = {}
    for m in MATS:
        for i, c in enumerate(st[m]): pal[f"{m}{i}"] = hexs(lab2rgb(lch(*c)))
    pal["eye"] = hexs(lab2rgb(lch(*st["eye"])))
    pal["outline"] = hexs(lab2rgb(lch(*st["outline"])))
    return pal

def p1_value(st):
    """Only lightness changes: even steps, stripes clearly darker than fur."""
    tgt = {"fur": [.34, .46, .58, .72], "belly": [.48, .62, .74, .86], "stripe": [.12, .18, .24, .30]}
    for m, Ls in tgt.items(): st[m] = [(L, c, h) for L, (_, c, h) in zip(Ls, st[m])]
    st["outline"] = (.12, st["outline"][1], st["outline"][2])

def p2_temperature(st):
    """Shadows drift cool and slightly more saturated, lights drift warm and lose chroma."""
    for m in ("fur", "belly"):
        out = []
        for i, (L, c, h) in enumerate(st[m]):
            t = i / 3
            h2 = h + (1 - t) * hue_delta(h, 300, 22) + t * hue_delta(h, 75, 14)
            out.append((L, c * (1.25, 1.15, 1.0, .75)[i], h2))
        st[m] = out
    st["stripe"] = [(L, c, h) for (L, c, h) in
                    [(L, (.05, .055, .05, .045)[i], 275) for i, (L, _, _) in enumerate(st["stripe"])]]
    st["outline"] = (.12, .04, 290)

def p3_chroma(st):
    """Mute the body; the eye becomes the only loud color."""
    st["fur"] = [(L, c * .55, h) for L, c, h in st["fur"]]
    st["belly"] = [(L, c * .5, h) for L, c, h in st["belly"]]
    st["eye"] = (.80, .15, 88)

def p4_mother(st):
    """One shared tint, the gold ground of the painting, added to every body color."""
    a0, b0 = .025 * math.cos(math.radians(REF_GROUND_H)), .025 * math.sin(math.radians(REF_GROUND_H))
    for m in MATS:
        out = []
        for L, c, h in st[m]:
            l = lch(L, c, h); out.append(to_lch((l[0], l[1] + a0, l[2] + b0)))
        st[m] = out

def p5_reference(st):
    """Keep our values; pull hue and chroma 70% of the way to the sampled painting."""
    for m in MATS:
        out = []
        for (L, c, h), r in zip(st[m], REF[m]):
            l = lch(L, c, h)
            out.append(to_lch((l[0], l[1] + .7 * (r[1] - l[1]), l[2] + .7 * (r[2] - l[2]))))
        st[m] = out

REF_GROUND_H = to_lch(GROUND_LAB)[2]

PASSES = [
    dict(id="base", title="Original palette", fn=None,
         changed="The palette from tiger.json: orange-salmon fur, pink belly, near-black stripes, golden eye. Stripes are now rendered (opt-in flag in render.py).",
         look="Grayscale on the gold ground: fur and ground sit at nearly the same value, so the sprite dissolves into the backdrop."),
    dict(id="value", title="Value structure", fn=p1_value,
         changed="Lightness only: four even steps per ramp, stripes well below the darkest fur, belly clearly lighter, darker outline. Hue and chroma untouched.",
         look="Squint. Do the stripes read? Are all four shading steps visible on the body? Is there a gap to the ground?"),
    dict(id="temperature", title="Temperature", fn=p2_temperature,
         changed="Fur and belly shadows drift toward violet and gain chroma; highlights drift toward yellow and lose it. Stripes become indigo instead of black; the outline turns indigo too.",
         look="Does form turn from warm to cool without relying on darkness alone?"),
    dict(id="chroma", title="Chroma budget", fn=p3_chroma,
         changed="Fur chroma cut by 45%, belly by 50%. The eye is raised to a high-chroma amber: the only loud color.",
         look="Mute everything mentally: does the eye still pull first, and does the body feel calm?"),
    dict(id="mother", title="Mother color", fn=p4_mother,
         changed="A small offset toward the painting's gold ground is added to fur, belly and stripes, so the tiger and its ground share a pigment.",
         look="Do the sprite and the gold feel like one painting rather than a cutout on a backdrop?"),
    dict(id="reference", title="Match the reference", fn=p5_reference,
         changed="Hue and chroma pulled 70% toward the colors sampled from the painting's tiger (mauve fur, indigo stripes); our values and our loud eye stay.",
         look="Compare against the painting itself. Where does the sprite still disagree: value, warmth, or saturation?"),
]


# ---------- render + metrics ----------
LIGHT = np.array([-0.45, 0.65, 0.62]); LIGHT /= np.linalg.norm(LIGHT)
GROUND_BG = tuple(REF["ground"]) + (255,)

def render_pass(cfg):
    nf = cfg["animations"]["walk"]["frames"]; size = cfg["render"]["size"]
    frames = {}
    for di in range(8):
        for f in range(nf):
            w = render.pose(cfg["skeleton"], cfg["animations"]["walk"]["bones"], f / nf)
            frames[(di, f)] = render.render_frame(cfg, w, di * 45, LIGHT)
    return frames, nf, size

def metrics(cfg, frames, st):
    pal = cfg["palette"]; outline = tuple(int(pal["outline"][i:i + 2], 16) for i in (0, 2, 4))
    px = []
    for di in range(8):
        a = np.array(frames[(di, 0)]).reshape(-1, 4)
        px.append(a[a[:, 3] > 0, :3])
    px = np.concatenate(px)
    px = px[~np.all(px == np.array(outline), axis=1)]
    cols, counts = np.unique(px, axis=0, return_counts=True)
    lab = rgb2lab(cols); w = counts / counts.sum()
    C = np.hypot(lab[:, 1], lab[:, 2])
    ab = REF_COLORS[:, 1:]
    chroma_dist = np.linalg.norm(lab[:, None, 1:] - ab[None], axis=2).min(1)
    def ramp_L(m): return [rgb2lab([int(pal[f"{m}{i}"][j:j + 2], 16) for j in (0, 2, 4)])[0] for i in range(4)]
    fur, stripe = ramp_L("fur"), ramp_L("stripe")
    h = lambda m, i: to_lch(rgb2lab([int(pal[f"{m}{i}"][j:j + 2], 16) for j in (0, 2, 4)]))[2]
    drift = abs(((h("fur", 3) - h("fur", 0) + 540) % 360) - 180)
    return {
        "colors": int(len(set(pal.values()))),
        "ref_dist": round(float((chroma_dist * w).sum() * 100), 1),
        "min_step": round(float(min(np.diff(fur)) * 100), 0),
        "ground_gap": round(float(abs(np.mean(fur[1:3]) - GROUND_LAB[0]) * 100), 0),
        "hue_drift": round(float(drift), 0),
        "loud": round(float((w * (C > .10)).sum() * 100), 1),
        "eye_chroma": round(float(to_lch(rgb2lab([int(pal["eye"][j:j + 2], 16) for j in (0, 2, 4)]))[1]), 3),
    }


def main():
    st = state_from_palette(cfg0["palette"])
    data = {"ground": hexs(REF["ground"]), "ref": {
        "fur": [hexs(lab2rgb(c)) for c in REF["fur"]], "belly": [hexs(lab2rgb(c)) for c in REF["belly"]],
        "stripe": [hexs(lab2rgb(c)) for c in REF["stripe"]], "eye": hexs(lab2rgb(REF["eye"])),
        "stats": REF["stats"]}, "passes": []}
    for n, p in enumerate(PASSES):
        if p["fn"]: p["fn"](st)
        cfg = copy.deepcopy(cfg0); cfg["palette"] = palette_from_state(st)
        frames, nf, size = render_pass(cfg)
        # 8 directions, frame 0, transparent
        strip = Image.new("RGBA", (size * 8, size), (0, 0, 0, 0))
        for di in range(8): strip.paste(frames[(di, 0)], (di * size, 0))
        strip.save(f"{OUT}/pass{n}_strip.png")
        # walk GIF, front-right, on the painting's ground
        gifs = []
        for f in range(nf):
            g = Image.new("RGBA", (size, size), GROUND_BG); g.alpha_composite(frames[(1, f)])
            gifs.append(g.resize((size * 4, size * 4), Image.NEAREST).convert("RGB"))
        gifs[0].save(f"{OUT}/pass{n}_walk.gif", save_all=True, append_images=gifs[1:], duration=110, loop=0)
        pal = cfg["palette"]
        data["passes"].append({
            "id": p["id"], "title": p["title"], "changed": p["changed"], "look": p["look"],
            "palette": {m: [pal[f"{m}{i}"] for i in range(4)] for m in MATS} | {"eye": pal["eye"], "outline": pal["outline"]},
            "metrics": metrics(cfg, frames, st),
        })
        print(n, p["title"], data["passes"][-1]["metrics"])
    with open(os.path.join(HERE, "data.js"), "w") as f:
        f.write("window.RECOLOR = " + json.dumps(data, indent=1) + ";\n")
    print("ref stats", REF["stats"], "ground", data["ground"])


if __name__ == "__main__":
    main()
