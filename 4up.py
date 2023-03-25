"""
booklet.py: Produce a 4-up sheet with four copies of the input page
"""
import io
import sys
from itertools import cycle
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


width, height = A4

transforms = [
	(0, 0, 0),
	(0.5, 0, 0),
	(0, 0.5, 0),
	(0.5, 0.5, 0)
]

def make_4up_page(in_doc, out_doc=None):
    page = PdfReader(in_doc).pages[0]  # Truncate overlength documents
    if out_doc is None:
        out_doc = io.BytesIO()
    canvas = Canvas(out_doc)
    canvas.setPageSize(A4)
    for (x, y, angle) in transforms:
        rl_page = makerl(canvas, pagexobj(page))
        canvas.saveState()
        canvas.translate(x*width, y*height)
        canvas.rotate(angle)
        canvas.scale(0.5, 0.5)
        canvas.doForm(rl_page)
        canvas.restoreState()
    canvas.showPage()
    canvas.save()
    out_doc.seek(0)
    return out_doc

if __name__ == '__main__':
    with open("VicRoadWeeds4up.pdf", "wb") as out_f:
        make_4up_page(sys.argv[1], out_f)
