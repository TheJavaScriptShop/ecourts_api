from flask import Flask, jsonify, request
import logging


app = Flask(__name__)


@app.route("/", methods=["POST"])
def ingress():
    logger = logging.getLogger("initial")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(
        f'local/logger/callback1.log', mode='a')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    body = request.json
    print(body["request"])
    logger.info(body)
    return jsonify({"status": True, "debugMessage": "Received"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
