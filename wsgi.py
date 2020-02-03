from cmec_backend import create_app
from cmec_backend.models import db, Scalar
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


def populate_db(scalar_data):
    regions = scalar_data["RESULTS"].keys()
    for region in regions:
        metrics = scalar_data["RESULTS"][region].keys()
        for metric in metrics:
            scalars = scalar_data["RESULTS"][region][metric].keys()
            for scalar in scalars:
                models = scalar_data["RESULTS"][region][metric][scalar].keys()
                for model in models:
                    try:
                        output = scalar_data["RESULTS"][region][metric][scalar][model]
                    except KeyError:
                        output = -999

                    print("{}-{}-{}-{} value: {}".format(region,
                                                         metric, scalar, model, output))
                    scalar_value = Scalar(
                        region=region,
                        metric=metric,
                        scalar=scalar,
                        model=model,
                        value=output
                    )
                    # Adds new User record to database
                    db.session.add(scalar_value)
        db.session.commit()  # Commits all changes


with app.app_context():
    data_file = "ilamb_data_hyperslab_format.json"
    # data_file = "test_ilamb_small.json"
    engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
    if app.config["ENV"] == "development" and not engine.dialect.has_table(engine, "scalars"):
        with open(os.path.join(app.static_folder, data_file)) as scalar_json:
            scalar_data = json.load(scalar_json)
            populate_db(scalar_data)
            print("Database populated")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
