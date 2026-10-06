"""Flask HTTP boundary. State and dispatch rules live in Model/Controller."""
import argparse
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from backend import LambdaBackend
from controller import Controller
from model import Model, StateError


def create_app(backend=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    controller = Controller(Model(), backend if backend is not None else LambdaBackend())
    app.extensions["controller"] = controller

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/state")
    def state():
        return jsonify(controller.state())

    @app.post("/api/source/<action>")
    def source(action):
        if action == "upload":
            uploaded = request.files.get("file")
            if uploaded is None:
                raise StateError("Choose a UTF-8 text file.")
            name = Path(uploaded.filename.replace("\\", "/")).name
            return jsonify(controller.upload(uploaded.read(), name, request.form.get("draft")))
        body = request.get_json()
        return jsonify(controller.change(action, draft=body.get("draft")))

    @app.post("/api/action/<operation>")
    def action(operation):
        body = request.get_json()
        return jsonify(controller.start(operation, draft=body.get("draft")))

    @app.errorhandler(StateError)
    def state_error(exc):
        return jsonify(error=str(exc), state=controller.state()), 409

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(exc):
        return jsonify(error="Request exceeds the 1 MiB transport limit; source limit is 65,536 bytes.",
                       state=controller.state()), 413

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    create_app().run(host="127.0.0.1", port=args.port, threaded=True, debug=False)
