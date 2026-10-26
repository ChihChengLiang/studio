#!/usr/bin/env python3
"""Render a JSON skeleton + primitive character to pixel-art sprites.

Pipeline: JSON (bones, boxes/ellipsoids, palette, animation channels)
  -> pose skeleton per frame -> orthographic ray-cast per pixel
  -> quantized lambert shading onto fixed palette ramps -> outlines
  -> 8 directions x N frames sprite sheet (+ GIFs).
No hand painting, no Blender.
"""
import argparse, json, math, os
import numpy as np
from PIL import Image

DIR_NAMES = ["front", "front-right", "right", "back-right",
             "back", "back-left", "left", "front-left"]


# ---------- math ----------
def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)

def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)

def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)

def mat4(R=None, t=None):
    M = np.eye(4)
    if R is not None: M[:3, :3] = R
    if t is not None: M[:3, 3] = t
    return M


# ---------- animation ----------
def wave(c, t):
    ph = 2 * math.pi * (t * c.get("freq", 1) + c.get("phase", 0))
    kind = c.get("wave", "none")
    v = {"none": 0.0, "sin": math.sin(ph), "cos": math.cos(ph),
         "abs": abs(math.sin(ph)), "relu": max(0.0, math.sin(ph))}[kind]
    return c.get("base", 0.0) + c.get("amp", 0.0) * v

def pose(skel, chans, t):
    """Return {bone: 4x4 model-space matrix}."""
    world = {}
    for b in skel:
        R = np.eye(3)
        tr = np.array(b["offset"], float)
        for c in chans.get(b["name"], []):
            v = wave(c, t)
            ax = c["axis"]
            if ax in "xyz":
                R = R @ {"x": rx, "y": ry, "z": rz}[ax](math.radians(v))
            else:  # tx / ty / tz
                tr[{"tx": 0, "ty": 1, "tz": 2}[ax]] += v
        local = mat4(R, tr)
        world[b["name"]] = (world[b["parent"]] @ local) if b["parent"] else local
    return world


# ---------- ray / primitive ----------
def hit_box(o, d, h):
    d = np.where(np.abs(d) < 1e-9, 1e-9, d)
    inv = 1.0 / d
    t1, t2 = (-h - o) * inv, (h - o) * inv
    tmin, tmax = np.minimum(t1, t2), np.maximum(t1, t2)
    tn, tf = tmin.max(1), tmax.min(1)
    hit = (tn <= tf) & (tf > 0)
    idx = tmin.argmax(1)
    n = np.zeros_like(o)
    n[np.arange(len(o)), idx] = -np.sign(d[idx])
    return hit, tn, n

def hit_ellipsoid(o, d, r):
    o, d = o / r, d / r
    a = d @ d
    b = o @ d
    c = (o * o).sum(1) - 1
    disc = b * b - a * c
    hit = disc >= 0
    t = (-b - np.sqrt(np.maximum(disc, 0))) / a
    p = o + t[:, None] * d            # in unit-sphere space
    n = p / r                          # gradient of x^2/r^2 in local space
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    return hit & (t > -50), t, n


# ---------- render ----------
def render_frame(cfg, world, yaw_deg, light):
    rs = cfg["render"]
    W = H = rs["size"]; S = rs["scale"]
    pitch = math.radians(rs["pitch"])
    pivot = np.array(rs["pivot"], float)
    Rv = rx(pitch) @ ry(math.radians(yaw_deg))
    V = mat4(Rv, -Rv @ pivot)

    jj, ii = np.meshgrid(np.arange(W), np.arange(H))
    px = (jj.ravel() + 0.5 - W / 2) / S
    py = (H / 2 - (ii.ravel() + 0.5)) / S
    P = np.stack([px, py, np.full_like(px, 20.0), np.ones_like(px)], 1)

    N = W * H
    zbuf = np.full(N, np.inf)
    nbuf = np.zeros((N, 3))
    mbuf = np.full(N, -1)

    mats = list(cfg["materials"].keys())
    for sh in cfg["shapes"]:
        Wb = world[sh["bone"]]
        loc = mat4(None, np.array(sh["center"], float))
        if "rot" in sh:
            r = sh["rot"]
            loc[:3, :3] = rx(math.radians(r[0])) @ ry(math.radians(r[1])) @ rz(math.radians(r[2]))
        M = V @ Wb @ loc
        Mi = np.linalg.inv(M)
        o = (P @ Mi.T)[:, :3]
        d = Mi[:3, :3] @ np.array([0, 0, -1.0])
        half = np.array(sh["size"], float) / 2
        if sh["type"] == "box":
            hit, t, n = hit_box(o, d, half)
        else:
            hit, t, n = hit_ellipsoid(o, d, half)
        upd = hit & (t < zbuf)
        zbuf[upd] = t[upd]
        nbuf[upd] = (M[:3, :3] @ n[upd].T).T
        mbuf[upd] = mats.index(sh["mat"])

    opaque = mbuf >= 0
    lam = nbuf @ light
    lvl = np.digitize(lam, [0.0, 0.35, 0.7])          # 0..3

    pal = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for k, v in cfg["palette"].items()}
    ramps = [[pal[n] for n in cfg["materials"][m]] for m in mats]
    out_col = pal["outline"]

    img = np.zeros((H, W, 4), np.uint8)
    lvl2, op2, m2 = lvl.reshape(H, W), opaque.reshape(H, W), mbuf.reshape(H, W)
    z2 = zbuf.reshape(H, W)

    # inner edges: a pixel sitting behind a clearly nearer neighbour drops to its darkest tone
    zp = np.pad(z2, 1, constant_values=np.inf)
    nearer = np.zeros((H, W), bool)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb = zp[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
        nearer |= (z2 - nb) > 0.12
    lvl2 = np.where(nearer, 0, lvl2)

    for y in range(H):
        for x in range(W):
            if op2[y, x]:
                img[y, x, :3] = ramps[m2[y, x]][lvl2[y, x]]
                img[y, x, 3] = 255

    # silhouette outline
    opp = np.pad(op2, 1)
    edge = np.zeros((H, W), bool)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        edge |= opp[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
    edge &= ~op2
    img[edge, :3] = out_col
    img[edge, 3] = 255
    return Image.fromarray(img, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("character", nargs="?", default="character.json")
    ap.add_argument("--anim", default="walk")
    ap.add_argument("--out", default="out")
    ap.add_argument("--zoom", type=int, default=4)
    a = ap.parse_args()

    cfg = json.load(open(a.character))
    os.makedirs(a.out, exist_ok=True)
    anim = cfg["animations"][a.anim]
    nf = anim["frames"]
    size = cfg["render"]["size"]
    light = np.array([-0.45, 0.65, 0.62]); light /= np.linalg.norm(light)

    frames = {}  # (dir, frame) -> image
    for di in range(8):
        for f in range(nf):
            world = pose(cfg["skeleton"], anim["bones"], f / nf)
            frames[(di, f)] = render_frame(cfg, world, di * 45, light)

    # sprite sheet: rows = directions, cols = frames
    sheet = Image.new("RGBA", (size * nf, size * 8), (0, 0, 0, 0))
    for (di, f), im in frames.items():
        sheet.paste(im, (f * size, di * size))
    sheet.save(f"{a.out}/{a.anim}_sheet.png")

    # preview on flat background, zoomed
    bg = Image.new("RGBA", sheet.size, (58, 66, 84, 255))
    bg.alpha_composite(sheet)
    bg.resize((bg.width * a.zoom // 2, bg.height * a.zoom // 2), Image.NEAREST).save(f"{a.out}/{a.anim}_sheet_preview.png")

    # GIF: all 8 directions in a 4x2 grid
    gifs = []
    Z = 3
    for f in range(nf):
        g = Image.new("RGBA", (size * 4, size * 2), (58, 66, 84, 255))
        for di in range(8):
            g.alpha_composite(frames[(di, f)], ((di % 4) * size, (di // 4) * size))
        gifs.append(g.resize((g.width * Z, g.height * Z), Image.NEAREST).convert("RGB"))
    gifs[0].save(f"{a.out}/{a.anim}_8dir.gif", save_all=True, append_images=gifs[1:], duration=110, loop=0)

    # palette check
    allowed = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for v in cfg["palette"].values()}
    used = set()
    for im in frames.values():
        arr = np.array(im).reshape(-1, 4)
        used |= {tuple(c[:3]) for c in arr[arr[:, 3] > 0]}
    print(f"colors used: {len(used)} / palette {len(allowed)}; all in palette: {used <= allowed}")
    print("saved to", a.out)


if __name__ == "__main__":
    main()
