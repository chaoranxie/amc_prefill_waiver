import zipfile
import os
from StringIO import StringIO

from flask import Flask
from flask import send_file
from flask import render_template
from flask import request, redirect, flash

from prefill_waiver import generate_pdfs_data, chunk_size, get_approved_participants

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

ALLOWED_EXTENSIONS = set(['csv'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            participants = get_approved_participants(file.stream)
            file_contents = generate_pdfs_data(
                waiver_pdf='static/waiver.pdf', approved_participants=participants, filled_waiver_base="filled_waiver_", chunk_size=chunk_size)
            in_memory = StringIO()
            zip = zipfile.ZipFile(in_memory, "a")
            for filename, content in file_contents.items():
                zip.writestr(filename, content)
            for file in zip.filelist:
                file.create_system = 0
            zip.close()
            in_memory.seek(0)
            return send_file(in_memory,
                             attachment_filename='filled_waivers.zip',
                             as_attachment=True)
        else:
            flash('Invalid file')
            return redirect(request.url)

    return render_template('home.html')


if __name__ == '__main__':
    app.run()
