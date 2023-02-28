from itertools import cycle
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

pages = PdfReader("test.pdf").pages[:8]

print(len(pages), "pages")

canvas = Canvas("out.pdf")
canvas.setPageSize(A4)

width, height = A4

transforms = [
	(0, 0.5, 0),
	(0.5, 0.5, 0),
	(1, 0.5, 180),
	(0.5, 0.5, 180)
]

page_numbers = (8, 1, 4, 5, 2, 7, 6, 3)

page_data = [(k, t) for (k, t) in zip(page_numbers, cycle(transforms))]

pdf_pages = []
page_ct = 0
for page_number, (x, y, angle) in page_data:
    page_ct += 1
    page = pages[page_number-1]
    page = makerl(canvas, pagexobj(page))
    pdf_pages.append(page)
    canvas.saveState()
    canvas.translate(x*width, y*height)
    canvas.rotate(angle)
    canvas.scale(0.5, 0.5)
    canvas.doForm(page)
    canvas.restoreState()
    if page_ct % 4 == 0:  # Assumes all 8 pages present ...
        canvas.showPage()
canvas.save()
