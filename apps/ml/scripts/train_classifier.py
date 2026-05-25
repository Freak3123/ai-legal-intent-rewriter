"""Train the TF-IDF + LogisticRegression baseline clause classifier.

Usage:
    uv run python -m scripts.train_classifier                  # seed CSV (fast)
    uv run python -m scripts.train_classifier --source cuad    # CUAD via HF

Reads:
    --source seed (default): apps/ml/data/clauses_seed.csv
    --source cuad:           datasets.load_dataset("theatticusproject/cuad-qa")

Writes:
    apps/ml/app/models/clause_classifier.pkl

The artifact is committed to the repo so the FastAPI service can load it at
startup without re-training on every cold start. Re-run this script when the
training data or hyperparameters change.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from scripts.cuad_label_map import map_category

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = REPO_ROOT / "data" / "clauses_seed.csv"
ARTIFACT_PATH = REPO_ROOT / "app" / "models" / "clause_classifier.pkl"


# -----------------------------------------------------------------------------
# Data loaders
# -----------------------------------------------------------------------------


def load_seed(path: Path) -> tuple[list[str], list[str]]:
    """Load the bundled hand-curated seed CSV."""
    texts: list[str] = []
    labels: list[str] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["label"])
    return texts, labels


# CUAD questions look like: "Highlight the parts (if any) of this contract
# related to "Document Name" that should be reviewed by a lawyer..."
_CUAD_CATEGORY_RE = re.compile(r'related to "([^"]+)"')


def _parse_cuad_category(question: str) -> str | None:
    m = _CUAD_CATEGORY_RE.search(question)
    return m.group(1) if m else None


_CUAD_DATA_URL = "https://github.com/TheAtticusProject/cuad/raw/main/data.zip"
_CUAD_CACHE_DIR = REPO_ROOT / "data" / ".cuad_cache"


def _download_cuad_zip() -> Path:
    """Download (and cache) the CUAD data.zip from the official GitHub mirror."""
    import urllib.request

    _CUAD_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = _CUAD_CACHE_DIR / "data.zip"
    if target.exists():
        print(f"  using cached {target.relative_to(REPO_ROOT)}")
        return target
    print(f"  downloading {_CUAD_DATA_URL} (~50 MB)…")
    urllib.request.urlretrieve(_CUAD_DATA_URL, target)  # noqa: S310 — hardcoded HTTPS URL
    print(f"  saved to {target.relative_to(REPO_ROOT)}")
    return target


_CUAD_JSON_RE = re.compile(r"CUAD_?v1.*\.json$", re.IGNORECASE)


def _extract_cuad_json(zip_path: Path) -> Path:
    """Find and extract the CUAD SQuAD-format JSON from the zip.

    The filename inside the archive has varied between releases ("CUAD_v1.json"
    vs "CUADv1.json"); match by regex.
    """
    import zipfile

    extract_dir = _CUAD_CACHE_DIR / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    cached = [p for p in extract_dir.rglob("*.json") if _CUAD_JSON_RE.search(p.name)]
    if cached:
        print(f"  using cached {cached[0].relative_to(REPO_ROOT)}")
        return cached[0]
    print("  extracting full-annotation JSON from data.zip…")
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if _CUAD_JSON_RE.search(Path(name).name):
                zf.extract(name, extract_dir)
                json_path = extract_dir / name
                print(f"  extracted {json_path.relative_to(REPO_ROOT)}")
                return json_path
    raise RuntimeError("No CUADv1*.json found inside data.zip")


def load_cuad(
    *,
    max_per_class: int = 800,
    min_text_length: int = 20,
    max_text_length: int = 2000,
    seed: int = 42,
) -> tuple[list[str], list[str]]:
    """Load CUAD and project onto the 12-bucket taxonomy.

    Skips the ``datasets`` library (its loader script support was dropped in
    v3) and parses CUAD_v1.json directly from the official GitHub release.
    Sampling is balanced per class up to ``max_per_class`` to avoid the OTHER
    bucket dominating.
    """
    import json
    import random

    print("loading CUAD from GitHub release…")
    zip_path = _download_cuad_zip()
    json_path = _extract_cuad_json(zip_path)

    with json_path.open(encoding="utf-8") as f:
        cuad = json.load(f)

    rng = random.Random(seed)  # noqa: S311 — sampling for ML, not crypto
    by_label: dict[str, list[str]] = defaultdict(list)
    skipped_no_answer = 0
    skipped_no_category = 0
    skipped_too_short = 0
    skipped_filtered = 0

    # SQuAD format: data → list of contracts → paragraphs → qas → answers
    for entry in cuad.get("data", []):
        for paragraph in entry.get("paragraphs", []):
            for qa in paragraph.get("qas", []):
                question = qa.get("question", "")
                answers = qa.get("answers", []) or []
                if not answers:
                    skipped_no_answer += 1
                    continue

                category = _parse_cuad_category(question)
                if category is None:
                    skipped_no_category += 1
                    continue

                label = map_category(category)
                if label is None:
                    skipped_filtered += 1
                    continue

                for ans in answers:
                    span = (ans.get("text") or "").strip()
                    if len(span) < min_text_length:
                        skipped_too_short += 1
                        continue
                    if len(span) > max_text_length:
                        span = span[:max_text_length]
                    by_label[label].append(span)

    texts: list[str] = []
    labels: list[str] = []
    for label, spans in by_label.items():
        rng.shuffle(spans)
        keep = spans[:max_per_class]
        texts.extend(keep)
        labels.extend([label] * len(keep))

    print(
        f"  raw CUAD examples retained: {sum(len(v) for v in by_label.values())}\n"
        f"  after balanced sampling   : {len(texts)}\n"
        f"  skipped (no answer)       : {skipped_no_answer}\n"
        f"  skipped (no category)     : {skipped_no_category}\n"
        f"  skipped (too short)       : {skipped_too_short}\n"
        f"  skipped (metadata filter) : {skipped_filtered}\n"
    )
    return texts, labels


# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,  # was 1 for tiny seed CSV; 2 reins in CUAD vocab
                    sublinear_tf=True,
                    lowercase=True,
                    strip_accents="unicode",
                    max_features=30_000,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    C=1.0,
                    solver="lbfgs",
                ),
            ),
        ]
    )


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=["seed", "cuad"],
        default="seed",
        help="Training data source. 'seed' uses the bundled CSV (fast). "
        "'cuad' downloads CUAD via HF datasets and applies the 41→12 map.",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=800,
        help="(cuad only) Max examples per class after balancing. Default 800.",
    )
    args = parser.parse_args()

    if args.source == "seed":
        if not SEED_PATH.exists():
            print(f"error: seed CSV not found at {SEED_PATH}", file=sys.stderr)
            return 1
        texts, labels = load_seed(SEED_PATH)
    else:
        # CUAD covers ~7 of our 12 labels. Always merge in the seed CSV so the
        # remaining labels (PAYMENT, CONFIDENTIALITY, DISPUTE_RESOLUTION,
        # DEFINITIONS, RENEWAL) are represented at all.
        texts, labels = load_cuad(max_per_class=args.max_per_class)
        if SEED_PATH.exists():
            seed_texts, seed_labels = load_seed(SEED_PATH)
            print(f"  + merging {len(seed_texts)} seed CSV examples")
            texts.extend(seed_texts)
            labels.extend(seed_labels)

    if not texts:
        print("error: no training data loaded", file=sys.stderr)
        return 1

    label_counts = Counter(labels)
    print(f"loaded {len(texts)} examples across {len(label_counts)} labels")
    for label, count in sorted(label_counts.items()):
        print(f"  {label:<22s} {count}")

    pipe = build_pipeline()

    min_count = min(label_counts.values())
    if min_count >= 3:
        cv = StratifiedKFold(n_splits=min(5, min_count), shuffle=True, random_state=42)
        preds = cross_val_predict(pipe, texts, labels, cv=cv)
        print("\nstratified CV report:")
        print(classification_report(labels, preds, zero_division=0))
    else:
        print(f"\nskipping CV (min class count {min_count} < 3)")

    pipe.fit(texts, labels)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, ARTIFACT_PATH, compress=3)
    size_kb = ARTIFACT_PATH.stat().st_size / 1024
    print(f"\nsaved {ARTIFACT_PATH.relative_to(REPO_ROOT)} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
