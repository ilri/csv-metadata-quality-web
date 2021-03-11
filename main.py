import os

from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["UPLOAD_EXTENSIONS"] = [".csv"]
app.config["UPLOAD_PATH"] = "uploads"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def upload_file():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)

    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config["UPLOAD_EXTENSIONS"]:
            abort(400)

        # make sure the upload directory exists
        try:
            os.mkdir(app.config["UPLOAD_PATH"])
        except FileExistsError:
            pass

        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filename))

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
