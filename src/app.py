import sys
from io import BytesIO
from flask import Flask, render_template, flash, send_file, redirect, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
from zipfile import ZipFile
from logging import getLogger
import pdfrw

from jinja2 import Environment, PackageLoader, select_autoescape


class PDF_Form(FlaskForm):
    file_details = FileField('file_details', validators=[DataRequired()])
    file_prefix = StringField('file_prefix')
    submit = SubmitField('Get Pages')


class WebFactionMiddleware(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = '/pz'
        return self.app(environ, start_response)


app = Flask(__name__)
app.config['SECRET_KEY'] = "lkjahskdflkjad[pouaerpoiuqt"
# app.wsgi_app = WebFactionMiddleware(app.wsgi_app)

env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

logger = getLogger(__name__)


@app.route("/", methods=['GET', 'POST'])
def get_or_post():
    form = PDF_Form()
    logger.info(f"Called")
    if form.validate_on_submit():
        my_file = request.files['file_details']
        file_prefix = request.form['file_prefix'] or 'page'
        try:
            inputpdf = pdfrw.PdfReader(fname=my_file.stream)
            outfiles = []
            outzip = BytesIO()
            container = ZipFile(outzip, 'w')
            for i, page in enumerate(inputpdf.pages):
                output = pdfrw.PdfWriter()
                file_name = f"{file_prefix}_{i+1:03}.pdf"
                output.addpage(page)
                outfile = BytesIO()
                output.write(outfile)
                container.writestr(f"pdf/{file_name}",
                                   outfile.getvalue())
            container.close()
            outzip.seek(0)
            return send_file(outzip,
                             mimetype="application/octet-stream",
                             as_attachment=True,
                             download_name="pages.zip")
        except Exception:
            flash(f"Could not open file as a PDF - please try again")
            raise
    return render_template('form.html', form=form)

if __name__ == '__main__':
    app.run()
