import os

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


@app.route("/process/<filename>")
def process_file(filename):
    return render_template("process.html", cli_version=cli_version, filename=filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
