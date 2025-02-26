from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_rdm = LocalProxy(lambda: current_app.extensions["oarepo-rdm"])
