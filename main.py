import os
import subprocess
import sys

from ansi2html import Ansi2HTMLConverter
from csv_metadata_quality.version import VERSION as cli_version
from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["UPLOAD_EXTENSIONS"] = [".csv"]
app.config["UPLOAD_PATH"] = "/tmp"


@app.route("/")
def index():
    return render_template("index.html", cli_version=cli_version)


@app.route("/", methods=["POST"])
def upload_file():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)

    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config["UPLOAD_EXTENSIONS"]:
            abort(400)

        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filename))

        return redirect(url_for("process_file", filename=filename))

    return "No file selected"


# TODO: probably use a base64- and URL-encoded version of the filename here so
# we can allow results to be saved and shared?
@app.route("/process/<filename>")
def process_file(filename):
    # do we need to use secure_filename again here?
    input_file = os.path.join(app.config["UPLOAD_PATH"], filename)
    # TODO: write an output file based on the input file name
    output_file = os.path.join(app.config["UPLOAD_PATH"], "test.csv")

    sys.argv = ["", "-i", input_file, "-o", output_file]

    # run subprocess and capture output as UTF-8 so we get a string instead of
    # bytes for ansi2html
    results = subprocess.run(
        ["csv-metadata-quality", "-i", input_file, "-o", output_file],
        capture_output=True,
        encoding="UTF-8",
    )
    # convert the output to HTML using ansi2html
    conv = Ansi2HTMLConverter()
    html = conv.convert(results.stdout)
    return render_template(
        "process.html", cli_version=cli_version, filename=filename, stdout=html
    )

    # I should remember this Flask-specific way to send files to the client
    # return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
