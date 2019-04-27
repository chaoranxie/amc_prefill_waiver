import logging
import os
import zipfile
from io import BytesIO, StringIO

from aws_xray_sdk.core import patch_all, xray_recorder
from flask import Flask, flash, redirect, render_template, request, send_file
from flask_cors import CORS

from prefill_waiver import (init_chunk_size, generate_pdfs_data, get_all_participants, get_approved_participants,
                            get_leaders)

xray_recorder.configure(context_missing='LOG_ERROR')
patch_all()

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.getLogger().setLevel(LOGLEVEL)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
CORS(app)

ALLOWED_EXTENSIONS = set(['csv'])

container_id = None


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def before_req():
    global container_id  # pylint: disable=W0603
    if container_id is None:
        context = request.environ['serverless.context']
        container_id = context.aws_request_id
    logger.info("container_id: %s", container_id)


@app.route('/api', methods=['POST'])
def api():
    file_stream = StringIO(request.json['csv'].encode("utf-8", 'ignore').decode())
    date = request.json['date']
    endDate = request.json.get('endDate')
    return get_zip_from_stream(file_stream, date, endDate)


def get_zip_from_stream(file_stream, date, endDate):
    participants = get_all_participants(file_stream)
    leaders = get_leaders(participants)
    participants = get_approved_participants(participants)
    file_contents = generate_pdfs_data(
        waiver_pdf='static/waiver.pdf',
        approved_participants=participants,
        filled_waiver_base="filled_waiver_",
        chunk_size=init_chunk_size,
        leaders=leaders,
        date=date,
        endDate=endDate)
    in_memory = BytesIO()
    zip_file = zipfile.ZipFile(in_memory, "a")
    for filename, content in file_contents.items():
        zip_file.writestr(filename, content)
    for file in zip_file.filelist:
        file.create_system = 0
    zip_file.close()
    in_memory.seek(0)
    response = send_file(in_memory, attachment_filename='filled_waivers.zip', as_attachment=True)
    return response


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
            file_stream = StringIO(file.stream.read().decode("utf-8"))
            return get_zip_from_stream(file_stream=file_stream, date=None, endDate=None)
        else:
            flash('Invalid file')
            return redirect(request.url)

    return render_template('home.html')


if __name__ == '__main__':
    app.run()
