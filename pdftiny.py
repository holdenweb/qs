from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import qrcode

data = """\
Part Name
Some sort of descriptive text
Another line of text
Another of these endless lines of text ...
and this is to see what the whole schemaozzle looks like""".splitlines()

fonts = ["Times-Bold"] + 3*["Helvetica"] + ["Courier"]
sizes = [18, 12, 12, 12, 6]
linepos = list(range(72, 10, -15))
c = canvas.Canvas("hello.pdf", pagesize=(3.5*inch, 1.4*inch))
c.rect(20, 10, 222, 83)
qc = qrcode.make("https://holdenweb.com/parts/{id}")
c.drawInlineImage(qc, 190, 40, width=50, height=50)
for font, size, pos, line in zip(fonts, sizes, linepos, data):
    c.setFont(font, size)
    c.drawString(25, pos, line)
c.showPage()
c.save()
