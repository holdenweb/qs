"""
booklet.py: Produce an 8-page booklet from a sibgle sheet of
paper printed on both sides.
"""
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

def main(args):
    if len(args) > 1:
        sys.exit("Just one file, please!")
    pages = PdfReader(args[0]).pages[:8]  # Truncate overlength documents
    canvas = Canvas("out.pdf")
    canvas.setPageSize(A4)
    for page_numbers in page_layouts:
        page_data = [(k, t) for (k, t) in zip(page_numbers, transforms)]
        for page_number, (x, y, angle) in page_data:
            if page_number <= len(pages):
                print("Setting page", page_number)
                page = pages[page_number-1]
                page = makerl(canvas, pagexobj(page))
                canvas.saveState()
                canvas.translate(x*width, y*height)
                canvas.rotate(angle)
                canvas.scale(0.5, 0.5)
                canvas.doForm(page)
                canvas.restoreState()
        print("Printing sheet")
        canvas.showPage()
    canvas.save()

if __name__ == '__main__':
    main(sys.argv[1:])
