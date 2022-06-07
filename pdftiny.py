from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import qrcode

def hello(c):
    c.rect(20, 10, 222, 83)
    c.setFont("Times-Bold", 18)
    c.drawString(25, 72, "Hello World")
    qc = qrcode.make("https://holdenweb.com/parts/{id}")
    c.drawInlineImage(qc, 190, 40, width=50, height=50)

c = canvas.Canvas("hello.pdf", pagesize=(3.5*inch, 1.4*inch))
hello(c)
c.showPage()
c.save()
