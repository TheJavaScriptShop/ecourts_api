from flask import Flask, jsonify, request


app = Flask(__name__)


@app.route("/", methods=["POST"])
def ingress():
    body = request.json
    return jsonify({"status": True, "debugMessage": "Received", "body": body})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
