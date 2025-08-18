import sys

WSGIPY_TEMPLATE = """\
from {name} import app, application

if __name__ == '__main__':
    app.run(port = {port}, debug = True)
"""
def create_wsgi(name, port=2400):
    with open("wsgi.py", 'w') as f:
        f.write(
            WSGIPY_TEMPLATE.format(
                name=name,
                port=port
            )
        )

def main():
    args = sys.argv[1:]
    create_wsgi(*args)

if __name__ == '__main__':
    main()
