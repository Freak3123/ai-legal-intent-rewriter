"""Generate slide assets from the REAL data in research_paper.txt.

Every number is reproduced verbatim from research_paper_final.docx.
Fonts and colours match the deck theme (Gill Sans MT; theme palette).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# --- deck theme: Gill Sans MT + theme colour palette --------------------
plt.rcParams['font.family'] = 'Gill Sans MT'
plt.rcParams['axes.unicode_minus'] = False

NAVY  = '#1A3260'   # accent1
BLUE  = '#4590B8'   # accent2
CYAN  = '#45CBE8'   # accent3
GREYC = '#969FA7'   # accent4
LGRN  = '#A2C777'   # accent5
GREEN = '#42955F'   # accent6
DK    = '#3D3D3D'   # dk2
LIGHT = '#EEF1F6'   # light navy tint
TINTG = '#E3F1E0'   # light green tint
TINTR = '#ECEEF0'   # light grey tint


# ---------------------------------------------------------------------------
# 1. EDA - training-set label distribution (research paper, Table 8)
# ---------------------------------------------------------------------------
def eda_label_distribution():
    labels = ['INTELLECTUAL_PROPERTY', 'LIABILITY', 'OTHER', 'INDEMNIFICATION',
              'GOVERNING_LAW', 'TERMINATION', 'WARRANTY', 'CONFIDENTIALITY',
              'DEFINITIONS', 'DISPUTE_RESOLUTION', 'PAYMENT', 'RENEWAL']
    counts = [806, 806, 806, 564, 468, 373, 181, 6, 6, 6, 6, 6]
    colours = [GREEN if c > 6 else GREYC for c in counts]

    fig, ax = plt.subplots(figsize=(12.6, 4.7), dpi=170)
    y = np.arange(len(labels))[::-1]
    ax.barh(y, counts, color=colours, edgecolor=NAVY, linewidth=0.6, height=0.66)
    for yi, c in zip(y, counts):
        ax.text(c + 12, yi, str(c), va='center', ha='left',
                fontsize=9.5, fontweight='bold', color=NAVY)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5, color=DK)
    ax.set_xlim(0, 900)
    ax.set_xlabel('Number of labelled clause examples', fontsize=10.5, color=DK)
    ax.set_title('Training-Set Label Distribution  -  4,034 clauses (CUAD + 72 seed)',
                 fontsize=13, fontweight='bold', pad=12, color=NAVY)
    ax.grid(axis='x', linestyle=':', alpha=0.5)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_color(GREYC)
    ax.tick_params(colors=GREYC)
    ax.legend(handles=[
        mpatches.Patch(facecolor=GREEN, edgecolor=NAVY,
                       label='CUAD-supported  (181-806 examples)'),
        mpatches.Patch(facecolor=GREYC, edgecolor=NAVY,
                       label='Seed-only  (6 examples each)')],
        loc='lower right', fontsize=9.5, frameon=True)
    fig.text(0.5, 0.005,
             'Source: research_paper_final.docx, Table 8.  Severe class imbalance - '
             'CUAD covers 7 of 12 categories well; 5 rely on seed data only.',
             ha='center', fontsize=9, style='italic', color=DK)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig('eda_label_distribution.png', facecolor='white', bbox_inches='tight')
    plt.close(fig)
    print('wrote eda_label_distribution.png')


# ---------------------------------------------------------------------------
# 2. Data preprocessing flow (research paper, Sec 3.1.2-3.1.4 / 4.4.1)
# ---------------------------------------------------------------------------
def preprocessing_flow():
    fig, ax = plt.subplots(figsize=(13.0, 3.4), dpi=170)
    ax.set_xlim(0, 100); ax.set_ylim(0, 30)
    ax.axis('off')
    stages = [
        ('CUAD release\nparsed',   '9,118 usable\nanswer spans',
         'Drop empty answers\n& spans < 20 chars', BLUE),
        ('Clean & map',            'Truncate spans\n> 2,000 chars',
         'Drop metadata cats;\nmap 41 CUAD to 12', NAVY),
        ('Balanced\nsampling',     '3,962 examples',
         'Cap of 800 spans\nper class',           NAVY),
        ('Merge\nseed set',        '+ 72 seed clauses',
         '6 hand-written\nexamples per class',    NAVY),
        ('Final training\nset',    '4,034 clauses',
         'Normalised text;\n12 categories',       GREEN),
    ]
    n = len(stages)
    box_w, gap = 16.5, 3.4
    x0 = (100 - (n * box_w + (n - 1) * gap)) / 2
    for i, (title, big, sub, colour) in enumerate(stages):
        x = x0 + i * (box_w + gap)
        ax.add_patch(FancyBboxPatch((x, 6), box_w, 18,
                     boxstyle='round,pad=0.3,rounding_size=1.1',
                     linewidth=1.5, edgecolor=colour, facecolor=LIGHT))
        cx = x + box_w / 2
        ax.text(cx, 21.0, title, ha='center', va='center',
                fontsize=10, fontweight='bold', color=NAVY)
        ax.text(cx, 15.4, big, ha='center', va='center',
                fontsize=11.5, fontweight='bold', color=colour)
        ax.text(cx, 9.4, sub, ha='center', va='center', fontsize=8.2, color=DK)
        if i < n - 1:
            ax.annotate('', xy=(x + box_w + gap, 15), xytext=(x + box_w, 15),
                        arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=2))
    ax.text(50, 28.4,
            'Data Preprocessing Pipeline  -  CUAD answer spans to a 4,034-clause training set',
            ha='center', va='center', fontsize=12.5, fontweight='bold', color=NAVY)
    ax.text(50, 1.8, 'Source: research_paper_final.docx, Sections 3.1.2-3.1.4 and 4.4.1.',
            ha='center', va='center', fontsize=8.6, style='italic', color=DK)
    fig.savefig('preprocessing_flow.png', facecolor='white', bbox_inches='tight')
    plt.close(fig)
    print('wrote preprocessing_flow.png')


# ---------------------------------------------------------------------------
# 3. Model-selection comparison (research paper, Sec 2.1.2 / 3.3 / 4)
# ---------------------------------------------------------------------------
def model_selection():
    fig = plt.figure(figsize=(12.6, 4.8), dpi=170)
    gs = fig.add_gridspec(2, 1, height_ratios=[4.4, 1.0], hspace=0.12)
    ax = fig.add_subplot(gs[0]); ax.axis('off')
    cols = ['Model', 'Pipeline role', 'Approach', 'Footprint', 'Decision']
    rows = [
        ['TF-IDF + Logistic Regression', 'Clause classifier',
         'Classical ML (scikit-learn)', '2 MB  -  CPU only', 'CHOSEN - current baseline'],
        ['Legal-BERT (base, uncased)', 'Clause classifier',
         'Domain pre-trained transformer', '~110M params  -  GPU', 'Planned - Phase 3'],
        ['DistilBERT', 'Clause classifier',
         'Distilled transformer', '~66M params', 'Considered - lighter alt.'],
        ['FLAN-T5-small', 'Intent rewriter',
         'Instruction-tuned seq2seq', '~80M params  -  GPU', 'Planned - Phase 3'],
        ['BART (base)', 'Intent rewriter',
         'Denoising seq2seq', '~140M params', 'Considered - alternative'],
        ['Zero-shot GPT-4', 'Clause classifier',
         'General-purpose LLM', 'API  -  no fine-tune', 'Rejected - see note'],
    ]
    row_colour = {0: TINTG, 5: TINTR}
    tbl = ax.table(cellText=rows, colLabels=cols, loc='center',
                   cellLoc='left', colLoc='left')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9.0)
    tbl.scale(1, 1.95)
    widths = [0.235, 0.14, 0.205, 0.20, 0.22]
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('#C7CDD6')
        cell.set_width(widths[c])
        if r == 0:
            cell.set_facecolor(NAVY)
            cell.set_text_props(color='white', fontweight='bold')
        else:
            cell.set_facecolor(row_colour.get(r - 1, 'white'))
            if c == 0:
                cell.set_text_props(fontweight='bold', color=NAVY)
            if c == 4 and (r - 1) in row_colour:
                cell.set_text_props(fontweight='bold')
    ax.set_title('Model Selection  -  Candidate Models for Classification and Rewriting',
                 fontsize=12.5, fontweight='bold', color=NAVY, pad=14)
    ax_note = fig.add_subplot(gs[1]); ax_note.axis('off')
    ax_note.text(0.5, 0.62,
                 'Decision: fine-tune a compact, domain-specific model rather than rely on a general LLM.',
                 ha='center', fontsize=9.7, fontweight='bold', color=NAVY)
    ax_note.text(0.5, 0.14,
                 'Evidence - cost-benefit study [12]: fine-tuned DeBERTa 87.8% vs zero-shot GPT-4 67.2% '
                 'accuracy on the CUAD single-label benchmark.\n'
                 'Current build uses the TF-IDF + Logistic Regression baseline (0.89 accuracy); '
                 'transformer fine-tuning is the planned next phase.',
                 ha='center', fontsize=8.7, style='italic', color=DK)
    fig.savefig('model_selection.png', facecolor='white', bbox_inches='tight')
    plt.close(fig)
    print('wrote model_selection.png')


# ---------------------------------------------------------------------------
# 4. Evaluation-metric formulae (research paper, Sec 3.5 / 4.4.1)
# ---------------------------------------------------------------------------
def metrics_formulae():
    fig, ax = plt.subplots(figsize=(12.2, 5.6), dpi=170)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis('off')
    items = [
        ('Precision', [(r'$Precision=\dfrac{TP}{TP+FP}$', 12.5)],
         'Predicted-positive clauses that are correct.'),
        ('Recall', [(r'$Recall=\dfrac{TP}{TP+FN}$', 12.5)],
         'True clauses of a class that are found.'),
        ('F1-score', [(r'$F_{1}=2\times\dfrac{Precision\times Recall}{Precision+Recall}$', 12)],
         'Harmonic mean of precision and recall.'),
        ('Accuracy', [(r'$Accuracy=\dfrac{TP+TN}{TP+TN+FP+FN}$', 12)],
         'All clauses classified correctly  =  0.89.'),
        ('Macro-average F1', [(r'$F_{1}^{\,macro}=\dfrac{1}{N}\sum_{i=1}^{N}F_{1,i}$', 12.5)],
         'Unweighted mean over N = 12 classes  =  0.56.'),
        ('Weighted-average F1', [(r'$F_{1}^{\,wt}=\sum_{i=1}^{N}\dfrac{n_{i}}{n}\,F_{1,i}$', 12.5)],
         'Per-class F1 weighted by support  =  0.89.'),
        ('TF-IDF feature weight',
         [(r'$w(t,d)=tf(t,d)\times idf(t)$', 11.5),
          (r'$idf(t)=\log\dfrac{1+n}{1+df(t)}+1$', 10.5)],
         'Classifier term weight (sublinear tf scaling).'),
    ]
    n = len(items)
    top, bot = 96, 5
    rh = (top - bot) / n
    for i, (name, formulas, desc) in enumerate(items):
        ytop = top - i * rh
        ycen = ytop - rh / 2
        ax.add_patch(FancyBboxPatch((4, ytop - rh + 0.9), 92, rh - 1.8,
                     boxstyle='round,pad=0.2,rounding_size=0.7',
                     linewidth=1.0, edgecolor='#C7CDD6',
                     facecolor=LIGHT if i % 2 == 0 else 'white'))
        ax.text(7.5, ycen + rh * 0.17, name, ha='left', va='center',
                fontsize=10.6, fontweight='bold', color=NAVY)
        ax.text(7.5, ycen - rh * 0.22, desc, ha='left', va='center',
                fontsize=8.4, style='italic', color=DK)
        if len(formulas) == 1:
            ax.text(72, ycen, formulas[0][0], ha='center', va='center',
                    fontsize=formulas[0][1], color='#111111')
        else:
            ax.text(72, ycen + rh * 0.18, formulas[0][0], ha='center',
                    va='center', fontsize=formulas[0][1], color='#111111')
            ax.text(72, ycen - rh * 0.22, formulas[1][0], ha='center',
                    va='center', fontsize=formulas[1][1], color='#111111')
    fig.text(0.5, 0.012,
             'Headline results measured under stratified k-fold cross-validation '
             '(research_paper_final.docx, Sec 3.5 and Table 9).',
             ha='center', fontsize=8.6, style='italic', color=DK)
    fig.savefig('metrics_formulae.png', facecolor='white', bbox_inches='tight')
    plt.close(fig)
    print('wrote metrics_formulae.png')


# ---------------------------------------------------------------------------
# 5. Two-service architecture diagram (docs/architecture.md)
# ---------------------------------------------------------------------------
def architecture_diagram():
    from matplotlib.patches import FancyArrowPatch
    fig, ax = plt.subplots(figsize=(8.0, 5.9), dpi=170)
    ax.set_xlim(0, 100); ax.set_ylim(0, 110)
    ax.axis('off')

    def node(x, y, w, h, title, body, colour):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                     boxstyle='round,pad=0.3,rounding_size=1.4',
                     linewidth=1.7, edgecolor=colour, facecolor=LIGHT))
        ax.text(x + w / 2, y + h - 4.0, title, ha='center', va='center',
                fontsize=9.3, fontweight='bold', color=NAVY)
        ax.text(x + w / 2, y + (h - 8) / 2 + 1.5, body, ha='center', va='center',
                fontsize=7.4, color=DK)

    def arrow(x1, y1, x2, y2, label):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                     mutation_scale=14, color=NAVY, lw=1.7))
        ax.text((x1 + x2) / 2 + 2.5, (y1 + y2) / 2, label, ha='left',
                va='center', fontsize=6.9, style='italic', color=DK)

    node(30, 86, 40, 12, "User's Browser",
         'Uploads PDF; pdf.js extracts\ntext client-side', BLUE)
    node(20, 58, 60, 16, 'Next.js 15 Web App  (Vercel)',
         'UI / dashboard - Auth.js v5 login\nUpload & polling routes - Mongoose ODM\nOrchestration', NAVY)
    node(2, 28, 44, 16, 'MongoDB Atlas  M0',
         'users - documents\nanalyses - clauses', GREEN)
    node(54, 28, 44, 16, 'FastAPI ML Service\n(Hugging Face Spaces)',
         'ingest - segment - classify\nNER - rewrite - risk flag', NAVY)
    node(54, 4, 44, 13, 'Hugging Face Hub',
         'Pinned / fine-tuned\nmodel checkpoints', GREYC)
    arrow(50, 86, 50, 74.5, 'HTTPS')
    arrow(38, 58, 24, 44.5, 'MongoDB URI')
    arrow(62, 58, 76, 44.5, 'HTTPS  /  JSON  (/v1)')
    arrow(76, 28, 76, 17.3, 'pulls on cold start')
    ax.text(50, 106, 'Two-Service System Architecture',
            ha='center', va='center', fontsize=12, fontweight='bold', color=NAVY)
    fig.savefig('architecture_diagram.png', facecolor='white', bbox_inches='tight')
    plt.close(fig)
    print('wrote architecture_diagram.png')


# ---------------------------------------------------------------------------
# 6. Six-stage model/pipeline architecture (research paper, Sec 3.3 / Table 4)
# ---------------------------------------------------------------------------
def model_architecture():
    import matplotlib.patches as mp
    fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=170)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis('off')
    stages = [
        ('1', 'INGEST',    'Text normalisation;\nPDF / OCR planned',      GREYC),
        ('2', 'SEGMENT',   'Regex markers +\nspaCy sentenciser',          GREEN),
        ('3', 'CLASSIFY',  'TF-IDF +\nLogistic Regression',               GREEN),
        ('4', 'NER',       'Regex extractors,\n6 entity types',           GREEN),
        ('5', 'REWRITE',   'Template now;\nFLAN-T5-small planned',        GREYC),
        ('6', 'RISK FLAG', '3-layer rule engine;\nlow / med / high',      GREEN),
    ]
    w, h = 28, 30
    xs = [18, 50, 82]
    ytop, ybot = 71, 27
    pos = {0: (xs[0], ytop), 1: (xs[1], ytop), 2: (xs[2], ytop),
           3: (xs[2], ybot), 4: (xs[1], ybot), 5: (xs[0], ybot)}
    for i, (num, name, tech, colour) in enumerate(stages):
        cx, cy = pos[i]
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                     boxstyle='round,pad=0.3,rounding_size=1.6',
                     linewidth=1.9, edgecolor=colour, facecolor=LIGHT))
        ax.add_patch(mp.Circle((cx - w / 2 + 3.6, cy + h / 2 - 3.6), 3.1,
                               color=colour, zorder=5))
        ax.text(cx - w / 2 + 3.6, cy + h / 2 - 3.6, num, ha='center',
                va='center', fontsize=8, fontweight='bold', color='white', zorder=6)
        ax.text(cx, cy + 5.6, name, ha='center', va='center',
                fontsize=10.2, fontweight='bold', color=NAVY)
        ax.text(cx, cy - 6.0, tech, ha='center', va='center', fontsize=7.6, color=DK)

    def arr(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=2.1))
    arr(xs[0] + w / 2, ytop, xs[1] - w / 2, ytop)
    arr(xs[1] + w / 2, ytop, xs[2] - w / 2, ytop)
    arr(xs[2], ytop - h / 2, xs[2], ybot + h / 2)
    arr(xs[2] - w / 2, ybot, xs[1] + w / 2, ybot)
    arr(xs[1] - w / 2, ybot, xs[0] + w / 2, ybot)
    ax.text(50, 97, 'Six-Stage NLP Pipeline  -  one pass per document',
            ha='center', fontsize=11.5, fontweight='bold', color=NAVY)
    ax.legend(handles=[
        mpatches.Patch(facecolor=LIGHT, edgecolor=GREEN, linewidth=1.9,
                       label='Implemented'),
        mpatches.Patch(facecolor=LIGHT, edgecolor=GREYC, linewidth=1.9,
                       label='Baseline - model upgrade planned')],
        loc='center', bbox_to_anchor=(0.5, 0.905), ncol=2, fontsize=8, frameon=False)
    ax.text(50, 4, 'Stages 3-6 (classify, NER, rewrite, risk-flag) execute once per clause.',
            ha='center', fontsize=8.4, style='italic', color=DK)
    fig.savefig('model_architecture.png', facecolor='white', bbox_inches='tight')
    plt.close(fig)
    print('wrote model_architecture.png')


if __name__ == '__main__':
    eda_label_distribution()
    preprocessing_flow()
    model_selection()
    metrics_formulae()
    architecture_diagram()
    model_architecture()
    print('All assets generated.')
