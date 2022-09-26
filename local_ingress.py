from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/", methods=["POST"])
def ingress():
    return jsonify({"status": True, "debugMessage": "Received"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
