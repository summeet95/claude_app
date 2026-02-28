"""
Download reference hairstyle images from external sources and upload to MinIO.

Sources:
  Male  — https://www.moderngentlemanmagazine.com/42-best-men-over-60-haircuts/
  Female — https://therighthairstyles.com/30-best-hairstyles-and-haircuts-for-women-over-60-to-suit-any-taste/

Writes /app/hairstyle_references/catalog.json on completion.
Run at worker startup via: python -m models.download_reference_images
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# ── Destination ──────────────────────────────────────────────────────────────

REFERENCES_DIR = Path("/app/hairstyle_references")
CATALOG_PATH = REFERENCES_DIR / "catalog.json"
BUCKET = "hairstyle-references"

# ── Source image lists ────────────────────────────────────────────────────────

_MGM = "https://www.moderngentlemanmagazine.com/wp-content/uploads/2024/12"
_TRH = "https://therighthairstyles.com/wp-content/uploads/2025/04"

MALE_IMAGES: dict[str, str] = {
    "timeless-taper-fade":           f"{_MGM}/Timeless-Taper-Fade-1-650x975.jpeg",
    "classic-crew-cut":              f"{_MGM}/Classic-Crew-Cut.jpeg",
    "short-caesar-cut":              f"{_MGM}/Short-Caesar-Cut.jpeg",
    "modern-pompadour":              f"{_MGM}/Modern-Pompadour-650x1156.jpeg",
    "ivy-league-cut":                f"{_MGM}/Ivy-League-Cut-650x1156.jpeg",
    "buzz-cut":                      f"{_MGM}/Buzz-Cut-650x1156.jpeg",
    "side-parted-comb-over":         f"{_MGM}/Side-Parted-Comb-Over.jpeg",
    "slicked-back-hairstyle":        f"{_MGM}/Slicked-Back-Hairstyle-650x650.jpeg",
    "long-and-layered":              f"{_MGM}/Long-and-Layered-e1734112726347-650x919.jpeg",
    "buzz-fade":                     f"{_MGM}/Buzz-Fade-650x1155.jpeg",
    "flat-top":                      f"{_MGM}/Flat-Top-650x813.jpeg",
    "textured-quiff":                f"{_MGM}/Textured-Quiff.jpeg",
    "bald-fade":                     f"{_MGM}/Bald-Fade-650x926.jpeg",
    "pompadour-fade":                f"{_MGM}/Pompadour-Fade-650x866.jpeg",
    "slicked-back-undercut":         f"{_MGM}/Slicked-Back-Undercut-650x1155.jpeg",
    "shaggy-cut":                    f"{_MGM}/Shaggy-Cut-e1734113125411.jpeg",
    "french-crop":                   f"{_MGM}/French-Crop-650x975.jpeg",
    "side-swept-layers":             f"{_MGM}/Side-Swept-Layers-650x975.jpeg",
    "curly-fade":                    f"{_MGM}/Curly-Fade-e1734113310533-650x914.jpeg",
    "angular-cut":                   f"{_MGM}/Angular-Cut-650x650.jpeg",
    "classic-bald-head":             f"{_MGM}/Classic-Bald-Head-e1734115286979-650x743.jpeg",
    "loose-side-part":               f"{_MGM}/Loose-Side-Part-e1734115332666-650x738.jpeg",
    "high-and-tight":                f"{_MGM}/High-and-Tight-650x975.jpeg",
    "long-slicked-back-hair":        f"{_MGM}/Long-Slicked-Back-Hair-650x1155.jpeg",
    "faux-hawk":                     f"{_MGM}/Faux-Hawk-650x975.jpeg",
    "the-bro-flow":                  f"{_MGM}/The-Bro-Flow.jpeg",
    "low-fade-with-sideburns":       f"{_MGM}/Low-Fade-with-Sideburns.jpeg",
    "buzz-cut-with-a-twist":         f"{_MGM}/Buzz-Cut-with-a-Twist-650x863.jpeg",
    "comb-over-textured-top":        f"{_MGM}/Comb-Over-with-Textured-Top-650x975.jpeg",
    "textured-crop":                 f"{_MGM}/Textured-Crop-650x1158.jpeg",
    "buzzed-pompadour":              f"{_MGM}/Buzzed-Pompadour-650x650.jpeg",
    "caesar-tapered-sides":          f"{_MGM}/Caesar-with-Tapered-Sides.jpeg",
    "medium-length-waves":           f"{_MGM}/Medium-Length-Waves.jpeg",
    "choppy-textured-crop":          f"{_MGM}/Choppy-Textured-Crop.jpeg",
    "side-swept-ivy-league":         f"{_MGM}/Side-Swept-Ivy-League.jpeg",
    "clean-shaven-bald":             f"{_MGM}/Clean-Shaven-Bald.jpeg",
    "mid-fade-with-part":            f"{_MGM}/Mid-Fade-with-Part.jpeg",
    "short-textured-waves":          f"{_MGM}/Short-Textured-Waves-650x975.jpeg",
    "military-buzz-cut":             f"{_MGM}/Military-Buzz-Cut.jpeg",
    "pompadour-tapered-fade":        f"{_MGM}/Pompadour-with-Tapered-Fade.jpeg",
    "textured-quiff-fade":           f"{_MGM}/Textured-Quiff-with-Fade-e1734114445422.jpeg",
    "slicked-back-pompadour-fade":   f"{_MGM}/Slicked-Back-Pompadour-with-Fade-e1734114550219-650x1056.jpeg",
}

FEMALE_IMAGES: dict[str, str] = {
    "undercut-bob":               f"{_TRH}/1-undercut-bob-hairstyle-for-women-over-60.jpg",
    "asymmetrical-bob":           f"{_TRH}/2-asymmetrical-bob-for-older-ladies.jpg",
    "curly-bob":                  f"{_TRH}/3-chin-length-curly-bob-for-women-over-60.jpg",
    "modern-pixie":               f"{_TRH}/4-over-60-modern-pixie-cut.jpg",
    "layered-shoulder-cut":       f"{_TRH}/5-shoulder-length-layered-cut-for-mature-ladies.jpg",
    "modern-shag":                f"{_TRH}/6-shag-hairstyle-for-women-over-60.jpg",
    "sharp-bob":                  f"{_TRH}/7-polished-blunt-bob-for-senior-ladies.jpg",
    "textured-pixie":             f"{_TRH}/8-piecey-pixie-hair-cut-for-women-over-60.jpg",
    "contemporary-crop":          f"{_TRH}/9-short-ut-for-midd-leaged-women.jpg",
    "sleek-undercut-pixie":       f"{_TRH}/10-over-60-long-top-undercut-pixie-hairdo.jpg",
    "graduated-bob":              f"{_TRH}/11-slimming-graduated-bob-for-mature-ladies.jpg",
    "short-shag":                 f"{_TRH}/12-shag-haircut-for-women-over-60.jpg",
    "modern-bowl-cut":            f"{_TRH}/13-bowl-cut-hair-style-for-women-over-60.jpg",
    "layered-lob":                f"{_TRH}/14-long-bob-with-layers-for-senior-women.jpg",
    "shoulder-length-shag":       f"{_TRH}/15-shoulder-length-shag-hairdo-for-women-over-60.jpg",
    "textured-medium-cut":        f"{_TRH}/16-medium-cut-hair-for-ladies-over-60.jpg",
    "blunt-mid-length-cut":       f"{_TRH}/17-mid-length-blunt-cut-for-mature-ladies.jpg",
    "neck-length-bob":            f"{_TRH}/18-over-60-bob-haircut-with-bangs.jpg",
    "collarbone-cut":             f"{_TRH}/19-collarbone-length-hairdo-for-older-women.jpg",
    "feathered-haircut":          f"{_TRH}/20-over-60-soft-feathered-hair-cut.jpg",
    "layered-long-cut":           f"{_TRH}/21-long-hair-cut-with-layers-for-ladies-over-60.jpg",
    "cascading-waves":            f"{_TRH}/22-over-60-long-layered-hair-style.jpg",
    "long-face-framing-cut":      f"{_TRH}/23-face-framing-long-haircut-for-women-over-60.jpg",
    "blunt-long-cut":             f"{_TRH}/24-sleek-long-blunt-cut-hairstyle-over-60.jpg",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        region_name="us-east-1",
    )


def _ensure_bucket(s3, bucket: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        s3.create_bucket(Bucket=bucket)
        print(f"[ref-dl] Created MinIO bucket: {bucket}")


def _download_image(url: str, dest: Path, retries: int = 3) -> bool:
    """Downloads url to dest. Returns True on success."""
    if dest.exists():
        return True
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": url.split("/wp-content")[0] + "/",
    }
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(resp.read())
            return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
            print(f"[ref-dl] Attempt {attempt+1}/{retries} failed for {url}: {exc}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return False


def _upload_to_minio(s3, local_path: Path, bucket: str, key: str) -> bool:
    try:
        s3.upload_file(str(local_path), bucket, key)
        return True
    except Exception as exc:
        print(f"[ref-dl] MinIO upload failed for {key}: {exc}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def run() -> None:
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing catalog so we can skip already-downloaded items
    catalog: dict[str, dict] = {}
    if CATALOG_PATH.exists():
        catalog = json.loads(CATALOG_PATH.read_text())

    s3 = _s3_client()
    _ensure_bucket(s3, BUCKET)

    all_images: list[tuple[str, str, str]] = [
        (slug, url, "male") for slug, url in MALE_IMAGES.items()
    ] + [
        (slug, url, "female") for slug, url in FEMALE_IMAGES.items()
    ]

    success_count = 0
    fail_count = 0

    for slug, url, gender in all_images:
        if slug in catalog:
            success_count += 1
            continue  # Already done

        ext = ".jpg" if url.endswith(".jpg") else ".jpeg"
        local_path = REFERENCES_DIR / gender / f"{slug}{ext}"
        minio_key = f"{gender}/{slug}{ext}"

        print(f"[ref-dl] Downloading {gender}/{slug} ...")
        ok = _download_image(url, local_path)
        if not ok:
            print(f"[ref-dl] SKIP {slug} — download failed, will use placeholder")
            fail_count += 1
            continue

        uploaded = _upload_to_minio(s3, local_path, BUCKET, minio_key)
        if uploaded:
            catalog[slug] = {
                "gender": gender,
                "local_path": str(local_path),
                "minio_key": minio_key,
            }
            success_count += 1
            print(f"[ref-dl] OK   {gender}/{slug}")
        else:
            # Still usable from local path even if MinIO upload failed
            catalog[slug] = {
                "gender": gender,
                "local_path": str(local_path),
                "minio_key": None,
            }
            success_count += 1
            fail_count += 1

    CATALOG_PATH.write_text(json.dumps(catalog, indent=2))
    print(
        f"[ref-dl] Done. {success_count} images ready, {fail_count} failed. "
        f"Catalog written to {CATALOG_PATH}"
    )


if __name__ == "__main__":
    run()
