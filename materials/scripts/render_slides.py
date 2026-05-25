"""Render selected slides of a .pptx to PNG via PowerPoint COM.
Usage: python render_slides.py <pptx> <slide,slide,...>
Attaches to the running PowerPoint; opens the file window-less and closes
only that presentation, leaving any user file untouched.
"""
import os
import sys
import win32com.client

pptx = os.path.abspath(sys.argv[1])
slides = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
outdir = os.path.join(os.path.dirname(pptx), 'rendered')
os.makedirs(outdir, exist_ok=True)

app = win32com.client.Dispatch('PowerPoint.Application')
pres = app.Presentations.Open(pptx, ReadOnly=True, WithWindow=False)
try:
    targets = slides or range(1, pres.Slides.Count + 1)
    for i in targets:
        out = os.path.join(outdir, f'chk_{i:02d}.png')
        pres.Slides(i).Export(out, 'PNG', 1600, 900)
        print('rendered', out)
finally:
    pres.Close()
print('done')
