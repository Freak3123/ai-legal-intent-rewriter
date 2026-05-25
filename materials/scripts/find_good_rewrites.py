# -*- coding: utf-8 -*-
"""Print rewriter output for a wider candidate pool so we can pick three good
examples for the figure. The FLAN-T5 model is biased toward TOS framings
because of its training corpus, so TOS-style inputs tend to rewrite better.
"""
from __future__ import annotations

import os
import re

os.environ.pop("LEGAL_REWRITER_DISABLE_HF", None)

CANDIDATES = [
    ("AUTO RENEWAL",
     "This Agreement shall automatically renew for successive one-year periods unless you "
     "provide written notice of cancellation at least thirty (30) days before the end of the "
     "then-current term."),
    ("PAYMENT",
     "Customer shall pay all undisputed invoices within thirty (30) days of receipt of a "
     "valid invoice from the Company; late payments shall accrue interest at one and "
     "one-half percent (1.5%) per month."),
    ("INDEMNIFICATION",
     "You agree to indemnify, defend and hold harmless the Company and its affiliates from "
     "and against any and all claims, damages, liabilities and expenses arising out of your "
     "use of the Services in violation of these Terms."),
    ("ARBITRATION",
     "Any dispute arising out of or in connection with this Agreement shall be finally "
     "resolved by binding arbitration administered by the American Arbitration Association "
     "under its rules."),
    ("WAIVER OF JURY",
     "Each party irrevocably waives any and all right to a trial by jury in any action, "
     "proceeding or counterclaim arising out of or relating to this Agreement."),
    ("MODIFICATION",
     "We reserve the right to modify these Terms at any time, and any such modifications "
     "shall become effective immediately upon posting to the Service."),
    ("USER CONTENT",
     "You grant the Company a worldwide, royalty-free, perpetual, irrevocable, "
     "non-exclusive licence to use, copy, modify, distribute and display the content you "
     "submit to the Service."),
    ("ACCOUNT TERMINATION",
     "The Company may suspend or terminate your account at any time, with or without notice "
     "and with or without cause, for any reason or no reason at all."),
    ("LIMITATION",
     "The Company's total cumulative liability under this Agreement shall not exceed the "
     "fees actually paid by the Customer in the twelve (12) months immediately preceding "
     "the event giving rise to the claim."),
    ("DATA SHARING",
     "We may share your personal information with our affiliates, service providers and "
     "business partners for purposes of providing and improving the Services."),
    ("GOVERNING LAW",
     "This Agreement shall be governed by and construed in accordance with the laws of the "
     "State of Delaware, without regard to its conflict of laws principles."),
    ("CHANGES",
     "We may, in our sole discretion, change, add or remove any portion of the Services or "
     "these Terms at any time, with or without notice to you."),
]


def main() -> None:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    repo = "freak3123/flan-t5-simplify-v1"
    tok = AutoTokenizer.from_pretrained(repo)
    model = AutoModelForSeq2SeqLM.from_pretrained(repo)
    model.eval()
    device = next(model.parameters()).device

    for label, legal in CANDIDATES:
        enc = tok("simplify legal: " + legal, return_tensors="pt",
                  max_length=384, truncation=True).to(device)
        with torch.no_grad():
            out = model.generate(**enc, max_length=192, num_beams=4,
                                 no_repeat_ngram_size=3, early_stopping=True)
        plain = tok.decode(out[0], skip_special_tokens=True).strip()
        # crude fidelity check: does any key noun from the input appear in the
        # output? Helpful for spotting hallucinations at a glance.
        nouns = re.findall(r"\b(?:agreement|terms|service|account|payment|invoice|"
                           r"interest|liability|claim|jury|arbitration|notice|renew|"
                           r"affiliate|content|jurisdiction|laws|delaware|fees|"
                           r"damages|indemnify|modify)\w*", legal, re.IGNORECASE)
        nouns_lc = {n.lower() for n in nouns}
        matches = sum(1 for n in nouns_lc if n in plain.lower())
        print(f"\n[{label}]  fidelity={matches}/{len(nouns_lc)}")
        print(f"  LEGAL:  {legal}")
        print(f"  PLAIN:  {plain}")


if __name__ == "__main__":
    main()
