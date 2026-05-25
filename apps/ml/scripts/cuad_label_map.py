"""Mapping from CUAD's 41 question categories to our 12-bucket taxonomy.

CUAD ("theatticusproject/cuad-qa") frames clause classification as QA: each
example has a question naming a category (e.g., "Highlight the parts (if any)
of this contract related to 'Cap On Liability'..."), with an answer span
pointing into the contract.

Three things happen here:
  1. Document-level metadata categories ("Document Name", "Parties",
     "Agreement Date", etc.) are skipped — they don't describe a clause.
  2. Each remaining category maps to one of our 12 labels. Mappings I'm
     unsure about land in OTHER (better than wrong).
  3. Anything not listed here is treated as OTHER as well, so adding more
     categories upstream won't break the loader.

Reference: https://huggingface.co/datasets/theatticusproject/cuad-qa
"""

from __future__ import annotations

from app.schemas import ClassificationLabel

# Categories that describe document-level metadata, not clause content.
# These are filtered out at load time.
SKIP_CATEGORIES: frozenset[str] = frozenset(
    {
        "Document Name",
        "Parties",
        "Agreement Date",
        "Effective Date",
        "Expiration Date",
        "Renewal Term",  # actually a clause; but CUAD spans are often dates → noisy
    }
)

# CUAD category → our 12-bucket label.
CUAD_TO_TAXONOMY: dict[str, ClassificationLabel] = {
    # --- LIABILITY ---
    "Cap On Liability": "LIABILITY",
    "Liquidated Damages": "LIABILITY",
    "Uncapped Liability": "LIABILITY",
    # --- TERMINATION ---
    "Termination For Convenience": "TERMINATION",
    "Notice Period To Terminate Renewal": "TERMINATION",
    # --- INDEMNIFICATION ---
    "Insurance": "INDEMNIFICATION",
    # --- INTELLECTUAL_PROPERTY ---
    "License Grant": "INTELLECTUAL_PROPERTY",
    "Non-Transferable License": "INTELLECTUAL_PROPERTY",
    "Affiliate License-Licensor": "INTELLECTUAL_PROPERTY",
    "Affiliate License-Licensee": "INTELLECTUAL_PROPERTY",
    "Unlimited/All-You-Can-Eat-License": "INTELLECTUAL_PROPERTY",
    "Irrevocable Or Perpetual License": "INTELLECTUAL_PROPERTY",
    "Source Code Escrow": "INTELLECTUAL_PROPERTY",
    "Post-Termination Services": "INTELLECTUAL_PROPERTY",
    "Ip Ownership Assignment": "INTELLECTUAL_PROPERTY",
    "Joint Ip Ownership": "INTELLECTUAL_PROPERTY",
    # --- GOVERNING_LAW ---
    "Governing Law": "GOVERNING_LAW",
    # --- CONFIDENTIALITY ---
    # CUAD doesn't have a direct "Confidentiality" category, but several
    # restrictive-covenant categories are functionally about non-disclosure.
    # Keep these in OTHER (see below) rather than overload CONFIDENTIALITY.
    # --- WARRANTY ---
    "Warranty Duration": "WARRANTY",
    # --- RENEWAL ---
    "Auto Renewal": "RENEWAL",
    # --- DISPUTE_RESOLUTION ---
    # No direct mapping in CUAD's category set; arbitration/dispute clauses
    # often surface as part of governing-law spans.
    # --- DEFINITIONS ---
    # CUAD doesn't tag definition clauses; leave as OTHER.
    # --- OTHER (everything else, explicitly listed for clarity) ---
    "Anti-Assignment": "OTHER",
    "Audit Rights": "OTHER",
    "Change Of Control": "OTHER",
    "Competitive Restriction Exception": "OTHER",
    "Covenant Not To Sue": "OTHER",
    "Exclusivity": "OTHER",
    "Minimum Commitment": "OTHER",
    "Most Favored Nation": "OTHER",
    "No-Solicit Of Customers": "OTHER",
    "No-Solicit Of Employees": "OTHER",
    "Non-Compete": "OTHER",
    "Non-Disparagement": "OTHER",
    "Price Restrictions": "OTHER",
    "Revenue/Profit Sharing": "OTHER",
    "Rofr/Rofo/Rofn": "OTHER",
    "Third Party Beneficiary": "OTHER",
    "Volume Restriction": "OTHER",
}


def map_category(category: str) -> ClassificationLabel | None:
    """Return the taxonomy label for a CUAD category, or None to skip."""
    cleaned = category.strip()
    if cleaned in SKIP_CATEGORIES:
        return None
    return CUAD_TO_TAXONOMY.get(cleaned, "OTHER")
