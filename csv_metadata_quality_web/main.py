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

app = application = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["UPLOAD_EXTENSIONS"] = [".csv"]
# the only place we can write to on Google App Engine is /tmp
# see: https://cloud.google.com/appengine/docs/standard/python3/using-temp-files
app.config["UPLOAD_PATH"] = "/tmp"


@app.route("/")
def index():
    return render_template("index.html", cli_version=cli_version)


@app.route("/", methods=["POST"])
def process():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)

    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config["UPLOAD_EXTENSIONS"]:
            abort(400)

        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filename))

        # generate a base64 representation of the filename to use as a slug
        base64name = b64encode(filename.encode("ascii"))

        # do we need to use secure_filename again here?
        input_file = os.path.join(app.config["UPLOAD_PATH"], filename)
        # write output file with the same name as the input file plus "-cleaned"
        output_file = os.path.join(
            app.config["UPLOAD_PATH"], os.path.splitext(filename)[0] + "-cleaned.csv"
        )

        args = ["-i", input_file, "-o", output_file]

        if "excludeCheckbox" in request.form:
            if "excludeText" in request.form:
                args.append("-x")
                args.append(request.form["excludeText"])

        if "agrovocCheckbox" in request.form:
            if "agrovocText" in request.form:
                args.append("-a")
                args.append(request.form["agrovocText"])

        if "unsafe" in request.form:
            args.append("-u")

        if "experimental" in request.form:
            args.append("-e")

        # Set cache dir to our upload path so we can tell csv-metadata-quality
        # to store its requests-cache database there instead of in the current
        # working directory (we can only write to /tmp on Google App Engine).
        # Also, make sure to keep our PATH!
        env = {
            "REQUESTS_CACHE_DIR": app.config["UPLOAD_PATH"],
            "PATH": os.environ["PATH"],
        }

        # run subprocess and capture output as UTF-8 so we get a string instead of
        # bytes for ansi2html
        results = subprocess.run(
            ["csv-metadata-quality"] + args,
            capture_output=True,
            encoding="UTF-8",
            env=env,
        )
        # convert the output to HTML using ansi2html
        conv = Ansi2HTMLConverter()
        stdout_html = conv.convert(results.stdout)

        # render the results to HTML so we can save them for later and allowing
        # the user to share the results page without posting the file again. We
        # decode base64name before sending it to convert it from bytes to str.
        results_html = render_template(
            "result.html",
            cli_version=cli_version,
            filename=filename,
            stdout=stdout_html,
            base64name=base64name.decode("ascii"),
        )
        # save results to a file so it's easy to have a saved results page when
        # we don't know the options a user used to POST the form.
        results_html_file = os.path.join(
            app.config["UPLOAD_PATH"], base64name.decode("ascii")
        )
        with open(results_html_file, "w") as fh:
            fh.write(results_html)

        return redirect(url_for("results", base64slug=base64name))

    return "No file selected"


@app.route("/result/<base64slug>")
def results(base64slug):
    results_html_file = os.path.join(app.config["UPLOAD_PATH"], base64slug)
    with open(results_html_file, "r") as fh:
        results_html = fh.read()

    return results_html


@app.route("/result/<base64slug>/download")
def result_download(base64slug):
    filename = b64decode(base64slug).decode("ascii")
    filename = secure_filename(os.path.splitext(filename)[0] + "-cleaned.csv")

    return send_from_directory(app.config["UPLOAD_PATH"], filename, as_attachment=True)
