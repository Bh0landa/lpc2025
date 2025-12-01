# Module `assets.py` — short description of this module.
import functools
import pygame as pg
from typing import Dict, Tuple, Any, List

# Helpers to render embedded pixel-frames into Surfaces with caching.
# Designed to be used by sprites to avoid per-frame pixel loops.

_cache: Dict[Tuple[str, int, int], pg.Surface] = {}

# Function `frame_to_surface(frame, target_w, target_h)` — describe purpose and behavior.


def frame_to_surface(frame: dict, target_w: int, target_h: int) -> pg.Surface:
    # Render a single embedded frame (dict with 'w','h','pixels') into a Surface of size (target_w,target_h).
    # Caches by (frame_name or id, target_w, target_h).
    if not isinstance(frame, dict) or "pixels" not in frame:
        raise ValueError("Invalid frame dict")
    name = frame.get("name", str(id(frame)))
    key = (name, target_w, target_h)
    if key in _cache:
        return _cache[key]
    w = int(frame["w"])
    h = int(frame["h"])
    pixels = frame["pixels"]
    surf0 = pg.Surface((w, h), pg.SRCALPHA)
    for y, row in enumerate(pixels):
        for x, col in enumerate(row):
            r, g, b, a = col
            if a == 0:
                continue
            surf0.set_at((x, y), (r, g, b, a))
    try:
        surf = pg.transform.smoothscale(surf0, (target_w, target_h))
    except Exception:
        surf = pg.transform.scale(surf0, (target_w, target_h))
    _cache[key] = surf
    return surf


# Function `frames_to_surfaces(frames, target_w, target_h)` — describe purpose and behavior.


def frames_to_surfaces(
    frames: List[dict], target_w: int, target_h: int
) -> List[pg.Surface]:
    out = []
    for fr in frames:
        try:
            out.append(frame_to_surface(fr, target_w, target_h))
        except Exception:
            # skip invalid frames
            pass
    return out


# Function `mask_from_surface(surf)` — describe purpose and behavior.


def mask_from_surface(surf: pg.Surface) -> pg.mask.Mask:
    # create mask and cache by surface id
    key = ("_mask_", id(surf))
    if key in _cache:
        return _cache[key]
    mask = pg.mask.from_surface(surf)
    _cache[key] = mask
    return mask
