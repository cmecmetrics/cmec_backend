from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json
from flask import current_app
from cmec_backend.models import db, Scalar

DATA_FILE = "ilamb_data_hyperslab_format.json"
# DATA_FILE = "test_ilamb_small.json"


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
                    # Adds new Scalar record to database
                    db.session.add(scalar_value)
        db.session.commit()  # Commits all changes


def main():
    with current_app.app_context():
        engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
        # if current_app.config["ENV"] == "development" and not engine.dialect.has_table(engine, "scalars"):
        with open(os.path.join(current_app.static_folder, DATA_FILE)) as scalar_json:
            scalar_data = json.load(scalar_json)
            populate_db(scalar_data)
            print("Database populated")


if __name__ == '__main__':
    main()
