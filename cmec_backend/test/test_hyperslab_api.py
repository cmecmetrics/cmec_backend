from cmec_backend import create_app
from cmec_backend.models import db, Scalar
import os
import json
import boto3

import logging

logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')

app = create_app()


def test_extract_scalar():
    result = session.query(Customers).filter(Customers.id == 2)
