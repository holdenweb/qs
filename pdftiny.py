from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def hello(c):
    for x in range(27):
        for y in range(10):
            x, y = x*10, y*10
            c.line(0, y, 270, y)
            c.line(x, 0, x, 200)
    c.drawString(20,20,"Hello World")
    c.drawString(40,40,"Hello World")
    c.drawString(60,60,"Hello World")

c = canvas.Canvas("hello.pdf", pagesize=(3.5*inch, 1.4*inch))
hello(c)
c.showPage()
c.save()
