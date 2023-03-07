"""
booklet.py: Produce an 8-page booklet from a single sheet of
paper printed duplex.
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
	(0, 0.5, 0),
	(0.5, 0.5, 0),
	(1, 0.5, 180),
	(0.5, 0.5, 180)
]

page_layouts = (8, 1, 4, 5), (2, 7, 6, 3)

def make_booklet(in_doc, out_doc=None):
    pages = PdfReader(in_doc).pages[:8]  # Truncate overlength documents
    if out_doc is None:
        out_doc = io.BytesIO()
    canvas = Canvas(out_doc)
    canvas.setPageSize(A4)
    for page_numbers in page_layouts:
        page_data = [(k, t) for (k, t) in zip(page_numbers, transforms)]
        for page_number, (x, y, angle) in page_data:
            if page_number <= len(pages):
                page = pages[page_number-1]
                page = makerl(canvas, pagexobj(page))
                canvas.saveState()
                canvas.translate(x*width, y*height)
                canvas.rotate(angle)
                canvas.scale(0.5, 0.5)
                canvas.doForm(page)
                canvas.restoreState()
        canvas.showPage()
    canvas.save()
    out_doc.seek(0)
    return out_doc

if __name__ == '__main__':
    with open("out.pdf", "wb") as out_f:
        make_booklet(sys.argv[1], out_f)
