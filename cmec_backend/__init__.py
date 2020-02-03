import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import redis
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

sess = Session()
db = SQLAlchemy()
ma = Marshmallow()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    # refers to application_top
    APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
    dotenv_path = os.path.join(APP_ROOT, '.env')
    load_dotenv(dotenv_path)

    # application configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI'),
        SQLALCHEMY_TRACK_MODIFICATIONS=os.environ.get(
            'SQLALCHEMY_TRACK_MODIFICATIONS'),
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize Plugins
    db.init_app(app)
    # login_manager.init_app(app)
    ma.init_app(app)
    sess.init_app(app)

    with app.app_context():
        from . import api
        app.register_blueprint(api.bp)

        # Create tables for our models
        db.create_all()

        # TODO: get all metrics, regions, etc and store in constants
        ALL_METRICS = {}
        for metric_name in db.session.query(Scalar.metric).distinct():
            ALL_METRICS[metric_name] = {}

        print("ALL_METRICS:", ALL_METRICS)

        return app
