from cmec_backend import create_app
from cmec_backend.models import db, Scalar
import cmec_backend.hyperslab_parse as hs_parse
import cmec_backend.init_database as init_database
import os
import json
import boto3
from sqlalchemy import Table, MetaData, create_engine

import logging

logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)


app = create_app()
with app.app_context():
    engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
    if app.config["ENV"] == "development" and not engine.dialect.has_table(engine, "scalars"):
        init_database.main()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
