from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import qrcode

data = """\
Part Name and/or
Descriptive Title
Another line of text in Helvetica
Another of these endless lines of text
to see what the whole schemozzle looks like""".splitlines()

fonts = ["Times-Bold"]*2 + ["Helvetica"] + ["Courier"]*2
sizes = [18, 18, 11, 8, 8]
linepos = [77 - n for n in (0, 20, 36, 52, 62)]
c = canvas.Canvas(file := BytesIO(),  pagesize=(3.5*inch, 1.4*inch))
c.rect(20, 10, 222, 83)
qc = qrcode.make("https://holdenweb.com/parts/{id}")
c.drawInlineImage(qc, 180, 30, width=60, height=60)
for font, size, pos, line in zip(fonts, sizes, linepos, data):
    c.setFont(font, size)
    c.drawString(25, pos, line)
c.showPage()
c.save()
with open("1hello.pdf", "wb") as out_file:
    out_file.write(file.getvalue())

