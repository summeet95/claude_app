"""
Query the hairstyle catalog from Postgres and rank styles
by compatibility with the detected head shape and user preferences.
Returns the top-N ranked styles.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import psycopg2
import psycopg2.extras

TOP_N = 10


@dataclass
class RankedStyle:
    style_id: str
    name: str
    slug: str
    score: float
    reasons: list[str]
    texture: str
    length: str
    maintenance: str
    barber_notes: str | None
    barber_guard: str | None
    top_length_cm: float | None


_SHAPE_COLUMN = {
    "oval": "compat_oval",
    "round": "compat_round",
    "square": "compat_square",
    "heart": "compat_heart",
    "oblong": "compat_oblong",
    "diamond": "compat_diamond",
}


def _get_conn():
    url = os.environ.get(
        "DATABASE_SYNC_URL",
        "postgresql://hairstyle:hairstyle_secret@postgres:5432/hairstyle_db",
    )
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def select_styles(
    head_shape: str,
    pref_gender: str | None = None,
    pref_length: str | None = None,
    pref_maintenance: str | None = None,
    hair_texture: str | None = None,
) -> list[RankedStyle]:

    shape_col = _SHAPE_COLUMN.get(head_shape, "compat_oval")

    conditions = []
    params: list[Any] = []
    if pref_gender:
        conditions.append("(gender = %s OR gender = 'unisex')")
        params.append(pref_gender)
    if pref_length:
        conditions.append("length = %s")
        params.append(pref_length)
    if pref_maintenance:
        conditions.append("maintenance = %s")
        params.append(pref_maintenance)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Bonus for matching hair texture
    texture_bonus = ""
    if hair_texture == "curly":
        texture_bonus = "+ bonus_curly_hair"
    elif hair_texture in ("straight",):
        texture_bonus = "+ bonus_fine_hair * 0.5"

    query = f"""
        SELECT
            id::text AS style_id,
            name, slug, texture, length, maintenance,
            barber_notes, barber_guard, top_length_cm,
            ({shape_col} {texture_bonus}) AS score
        FROM hairstyle_catalog
        {where_clause}
        ORDER BY score DESC
        LIMIT %s
    """
    params.append(TOP_N)

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    results: list[RankedStyle] = []
    for row in rows:
        reasons = _build_reasons(head_shape, row["texture"], hair_texture)
        results.append(
            RankedStyle(
                style_id=row["style_id"],
                name=row["name"],
                slug=row["slug"],
                score=float(row["score"]),
                reasons=reasons,
                texture=row["texture"],
                length=row["length"],
                maintenance=row["maintenance"],
                barber_notes=row["barber_notes"],
                barber_guard=row["barber_guard"],
                top_length_cm=row["top_length_cm"],
            )
        )

    print(f"[style_selector] Selected {len(results)} styles for shape={head_shape}")
    return results


def _build_reasons(head_shape: str, style_texture: str, user_texture: str | None) -> list[str]:
    reasons = []
    shape_tips = {
        "oval": "Oval faces suit virtually any style",
        "round": "This style adds height to balance a round face",
        "square": "Softened layers complement a square jaw",
        "heart": "Volume at the chin balances a wider forehead",
        "oblong": "Width-adding styles shorten an elongated face",
        "diamond": "Fullness at forehead and chin frames a diamond face",
    }
    if head_shape in shape_tips:
        reasons.append(shape_tips[head_shape])
    if user_texture and user_texture == style_texture:
        reasons.append(f"Works great with your {user_texture} hair texture")
    return reasons
