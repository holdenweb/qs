import os
import io
import sys
from io import BytesIO
from booklet import make_booklet
from flask import (Blueprint, Flask, Response, render_template, flash,
                   send_file, redirect, request, url_for)
from flask_wtf import FlaskForm
import qrcode
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
from zipfile import ZipFile
from logging import getLogger
import pdfrw
from jinja2 import Environment, FileSystemLoader, select_autoescape

class PDF_Form(FlaskForm):
    file_details = FileField('file_details', validators=[DataRequired()])
    file_prefix = StringField('file_prefix')
    submit = SubmitField('Get Pages')

class QRcode_Form(FlaskForm):
    qrcode_text = StringField('qrcode_text')
    submit = SubmitField('Get QR Code')

class BookletForm(FlaskForm):
    file_details = FileField('file_details', validators=[DataRequired()])
    submit = SubmitField("Generate Booklet")


child = Blueprint('child', __name__, url_prefix='/child')
@child.route("/page")
def child_page():
    return "This is the child page"

parent = Blueprint('parent', __name__, url_prefix='/parent')
@parent.route("/page")
def parent_page():
    return render_template('base.html', content=
    """
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb rhubarb
""")

appfile_dir = os.path.dirname(__file__)
app = Flask(__name__)
parent.register_blueprint(child)
app.register_blueprint(parent)



env = Environment(
    loader=FileSystemLoader('%s/templates/' % appfile_dir),
    autoescape=select_autoescape(['html', 'xml'])
)
logger = getLogger(__name__)


@app.route("/")
def home_page():
    return render_template("basepage-layoutit.html")

#static_redirect("/images/")
#static_redirect("/css/styles.css")

@app.route("/pdf/pagezip", methods=['GET', 'POST'])
def get_or_post_pdf():
    form = PDF_Form()
    logger.info(f"Page split requested")
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
    return render_template('pagesplit_form.html', form=form)


@app.route("/pdf/booklet", methods=['GET', 'POST'])
def get_or_post_booklet():
    form = BookletForm()
    logger.info("Booklet requested")
    if form.validate_on_submit():
        my_file = request.files['file_details']
        try:
            output_pdf = make_booklet(my_file.stream)
            return Response(output_pdf, mimetype="application.pdf")
        except Exception as e:
            return f"I'm sorry, Dave, it seems I couldn't do that:\n{e}"
    return render_template('booklet_form.html', form=form)

@app.route("/qrcode", methods=['GET', 'POST'])
def get_or_post_qrcode():
    form = QRcode_Form()
    logger.info("QR code requested")
    if form.validate_on_submit():
        text = request.form['qrcode_text']
        qr = qrcode.make(text)
        memfile = io.BytesIO()
        qr.save(memfile)
        memfile.seek(0)
        response = Response(memfile.getvalue(), mimetype="image/gif")
        return response
    return render_template('qrcode_form.html', form=form)

app.config['SECRET_KEY'] = "lkjahskdflkjad[pouaerpoiuqt"
application = app.wsgi_app

if __name__ == '__main__':

    def has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    @app.route("/r", methods=['GET'])
    def site_map():
        result = ""
        for rule in app.url_map.iter_rules():
            # Filter out rules we can't navigate to in a browser
            # and rules that require parameters
            if "GET" in rule.methods and has_no_empty_params(rule):
                url = url_for(rule.endpoint, **(rule.defaults or {}))
                result += f"URL: {url}, endpoint: {rule.endpoint}/<br>\n"
                # links is now a list of url, endpoint tuples
            return result
        result = site_map()
        print(result)
        return(result)

    app.run(port=2400)
