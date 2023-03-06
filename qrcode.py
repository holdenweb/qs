import qrcode

qc = qrcode.make("https://holdenweb.com/parts/{id}")

def qrcode(text):
    return qrcode.make(text)