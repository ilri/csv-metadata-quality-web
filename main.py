import os
import subprocess
from base64 import b64decode, b64encode

from ansi2html import Ansi2HTMLConverter
from csv_metadata_quality.version import VERSION as cli_version
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
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

        # generate a base64 representation of the filename to use as a slug
        base64name = b64encode(filename.encode("ascii"))

        return redirect(url_for("process_file", base64slug=base64name))

    return "No file selected"


@app.route("/result/<base64slug>")
def process_file(base64slug):
    # get filename from base64-encoded slug
    filename = b64decode(base64slug).decode("ascii")

    # do we need to use secure_filename again here?
    input_file = os.path.join(app.config["UPLOAD_PATH"], filename)
    # write output file with the same name as the input file plus "-cleaned"
    output_file = os.path.join(
        app.config["UPLOAD_PATH"], os.path.splitext(filename)[0] + "-cleaned.csv"
    )

    args = ["-i", input_file, "-o", output_file]

    # run subprocess and capture output as UTF-8 so we get a string instead of
    # bytes for ansi2html
    results = subprocess.run(
        ["csv-metadata-quality"] + args,
        capture_output=True,
        encoding="UTF-8",
    )
    # convert the output to HTML using ansi2html
    conv = Ansi2HTMLConverter()
    html = conv.convert(results.stdout)
    return render_template(
        "result.html",
        cli_version=cli_version,
        filename=filename,
        stdout=html,
        base64name=base64slug,
    )


@app.route("/result/<base64slug>/download")
def result_download(base64slug):
    filename = b64decode(base64slug).decode("ascii")
    filename = secure_filename(os.path.splitext(filename)[0] + "-cleaned.csv")

    return send_from_directory(app.config["UPLOAD_PATH"], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
