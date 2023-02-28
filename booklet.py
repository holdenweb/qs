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

page_numbers = (8, 1, 5, 4, 2, 7, 3, 6)

page_data = {k: t for (k, t) in zip(page_numbers, cycle(transforms))}

pdf_pages = []
for page_number, page in enumerate(pages, 1):
    x, y, angle = page_data[page_number]
    print(page_number, x, y, angle)
    page = makerl(canvas, pagexobj(page))
    pdf_pages.append(page)
    canvas.saveState()
    canvas.translate(x*width, y*height)
    print("Translating by", x*width, y*height)
    canvas.rotate(angle)
    print("Rotating by", angle)
    canvas.scale(0.5, 0.5)
    canvas.doForm(page)
    canvas.restoreState()
    if page_number % 4 == 0:
        canvas.showPage()
canvas.save()
