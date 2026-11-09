import logging
from .app import create_app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)
