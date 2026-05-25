"""Generate the Results chart from measured CV metrics (research paper, Table 9).
Theme-matched: Gill Sans MT font, deck colour palette. No overlapping text."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.family'] = 'Gill Sans MT'
plt.rcParams['axes.unicode_minus'] = False

NAVY, BLUE, GREEN, GREYC, DK = '#1A3260', '#4590B8', '#42955F', '#969FA7', '#3D3D3D'

# Measured values reproduced verbatim from research_paper_final.docx, Table 9.
classes = ['GOVERNING_LAW', 'INDEMNIFICATION', 'LIABILITY', 'TERMINATION',
           'INTELLECTUAL_PROPERTY', 'WARRANTY', 'OTHER',
           'CONFIDENTIALITY', 'DEFINITIONS', 'DISPUTE_RESOLUTION',
           'PAYMENT', 'RENEWAL']
precision = [0.99, 0.97, 0.95, 0.89, 0.87, 0.78, 0.77, 0.50, 0.00, 0.00, 0.00, 0.00]
recall    = [0.97, 0.95, 0.88, 0.92, 0.83, 0.91, 0.86, 0.33, 0.00, 0.00, 0.00, 0.00]
f1        = [0.98, 0.96, 0.91, 0.91, 0.85, 0.84, 0.81, 0.40, 0.00, 0.00, 0.00, 0.00]
support   = [468, 564, 806, 373, 806, 181, 806, 6, 6, 6, 6, 6]
accuracy, weighted_f1, macro_f1 = 0.89, 0.89, 0.56

fig = plt.figure(figsize=(15, 5.9), dpi=170)
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 4.8], hspace=0.30)

# --- top strip: summary metric cards ---
ax_top = fig.add_subplot(gs[0])
ax_top.axis('off'); ax_top.set_xlim(0, 1); ax_top.set_ylim(0, 1)


def metric_box(x, label, value, colour):
    ax_top.add_patch(mpatches.FancyBboxPatch(
        (x, 0.10), 0.20, 0.78, boxstyle='round,pad=0.02',
        linewidth=1.2, edgecolor=colour, facecolor='#EEF1F6'))
    ax_top.text(x + 0.10, 0.62, value, ha='center', va='center',
                fontsize=22, fontweight='bold', color=NAVY)
    ax_top.text(x + 0.10, 0.25, label, ha='center', va='center',
                fontsize=11, color=DK)


metric_box(0.06, 'Overall Accuracy',    '0.89',    NAVY)
metric_box(0.30, 'Weighted-Average F1', '0.89',    GREEN)
metric_box(0.54, 'Macro-Average F1',    '0.56',    GREYC)
metric_box(0.78, 'Automated Tests',     '34 / 34', BLUE)

# --- grouped bar chart: per-class precision / recall / F1 ---
ax = fig.add_subplot(gs[1])
x = np.arange(len(classes))
width = 0.26
ax.bar(x - width, precision, width, label='Precision',
       color=NAVY, edgecolor=NAVY, linewidth=0.5)
ax.bar(x, recall, width, label='Recall',
       color=BLUE, edgecolor=NAVY, linewidth=0.5)
ax.bar(x + width, f1, width, label='F1-score',
       color=GREEN, edgecolor=NAVY, linewidth=0.5)

for xi, v in zip(x, f1):
    ax.text(xi + width, v + 0.02, f'{v:.2f}', ha='center', va='bottom',
            fontsize=8, color=GREEN)

# support count folded into the x tick label -> no separate overlapping text
ax.set_xticks(x)
ax.set_xticklabels([f'{c}\n(n={s})' for c, s in zip(classes, support)],
                   rotation=22, ha='right', fontsize=8.6, color=DK)
ax.set_ylim(0, 1.12)
ax.set_ylabel('Score', fontsize=11, color=DK)
ax.set_title('Per-Class Classifier Performance under Stratified Cross-Validation',
             fontsize=13, fontweight='bold', pad=10, color=NAVY)
ax.axhline(0.80, color=GREYC, linestyle='--', linewidth=1.0)
ax.text(len(classes) - 0.45, 0.82, 'Project target: F1 = 0.80',
        ha='right', va='bottom', fontsize=8.5, color=DK, style='italic')
ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))
ax.grid(axis='y', linestyle=':', alpha=0.5)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_color(GREYC)
ax.tick_params(colors=GREYC)
ax.legend(loc='upper right', frameon=True, fontsize=10)

fig.savefig('results_chart.png', bbox_inches='tight', facecolor='white')
print('wrote results_chart.png')
