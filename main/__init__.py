import logging
import zipfile,io,json
import tempfile
import azure.functions as func
from flask import Flask, send_file,jsonify,Response,request,render_template
from os import listdir
import os

app = Flask(__name__)

logging.basicConfig(
    filename='log.txt',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'

)

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Each request is redirected to the WSGI handler.
    """
    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)


@app.route("/home", methods=['GET'])
def index():
    logging.info("Application Started")
    return render_template('index.html')


@app.route("/zip", methods=['GET','POST'])
def download_zip():
    if request.method == 'POST':
            try:
                body = request.data
                body = json.loads(body)
                data = io.BytesIO()
                with zipfile.ZipFile(data, mode='w') as zf:
                    for file in body:
                        zf.writestr(file["name"], file["content"])
                        logging.info("File Added to Zip" + file["name"])
                data.seek(0)
                return send_file(data, as_attachment=True, download_name="ZippedFile.zip", mimetype="application/zip")
            except Exception as e:
                logging.error(e)
                return "Error Occurred"
    else:
        return "Please send a post request with a file"

    


if __name__ == '__main__':
    app.run(debug=False)
