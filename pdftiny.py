from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import qrcode

def hello(c):
    for x in range(27):
        for y in range(10):
            x, y = x*10, y*10
            c.line(0, y, 270, y)
            c.line(x, 0, x, 200)
    c.drawString(20,20,"Hello World")
    qc = qrcode.make("https://holdenweb.com/")
    qc.save("qrcode.gif")
    c.drawImage("qrcode.gif", 190, 40, width=50, height=50)

c = canvas.Canvas("hello.pdf", pagesize=(3.5*inch, 1.4*inch))
hello(c)
c.showPage()
c.save()
