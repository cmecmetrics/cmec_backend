import json
import logging
import os
from flask import Blueprint, render_template, current_app, request, jsonify, Response, make_response, send_file, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, MetaData, create_engine
from flask_cors import CORS
from cmec_backend.models import db, Scalar, ScalarSchema
import pprint
import copy


engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))

bp = Blueprint('api', __name__, url_prefix='/api')

# TODO: get all metrics, regions, etc and store in constants
ALL_METRICS = {}
for metric_name in db.session.query(Scalar.metric).order_by(Scalar.metric).distinct():
    ALL_METRICS[metric_name[0]] = {}

# print("ALL_METRICS:", ALL_METRICS)
# print("ALL_METRICS type:", type(ALL_METRICS))

ALL_REGIONS = {}
for region_name in db.session.query(Scalar.region).order_by(Scalar.region).distinct():
    ALL_REGIONS[region_name[0]] = {}

# print("ALL_REGIONS:", ALL_REGIONS)

ALL_MODELS = {}
for model_name in db.session.query(Scalar.model).order_by(Scalar.model).distinct():
    ALL_MODELS[model_name[0]] = {}

# print("ALL_MODELS:", ALL_MODELS)

ALL_SCALARS = {}
for scalar_name in db.session.query(Scalar.scalar).order_by(Scalar.scalar).distinct():
    ALL_SCALARS[scalar_name[0]] = {}

# print("ALL_SCALARS:", ALL_SCALARS)


def build_hyperslab_structure(json_object, region, metric, scalar, model):
    # hyperslab_structure = dict()
    # hyperslab_structure.clear()
    json_object.clear()
    if region:
        hyperslab_structure = {region: {}}
    else:
        hyperslab_structure = ALL_REGIONS

    regions = hyperslab_structure.keys()
    if not metric:
        for region in regions:
            hyperslab_structure[region] = copy.deepcopy(ALL_METRICS)

    print("hyperslab_structure:", hyperslab_structure)

    # Try returning deepcopy of hyperslab_structure
    return hyperslab_structure


@bp.route("/hyperslab", methods=["POST"])
def hyperslab():
    hyperslab_structure = {}
    print("hyperslab_structure at beginning:", hyperslab_structure)
    # hyperslab_structure.clear()
    data = request.json
    region_param, metric, scalar, model = [
        data["region"], data["metric"], data["scalar"], data["model"]]

    if region_param:
        region_param = region_param["value"]
        print("region_param:", region_param)
        # region_value = region_param["value"]
        # print("region_value:", region_value)
        hyperslab_structure = {region_param: {}}
    else:
        hyperslab_structure = copy.deepcopy(ALL_REGIONS)

    print("hyperslab_structure after region:", hyperslab_structure)

    regions = hyperslab_structure.keys()
    if not metric:
        for region_name in regions:
            hyperslab_structure[region_name] = copy.deepcopy(ALL_METRICS)

    # print("hyperslab_structure after metric:", hyperslab_structure)
    # print("ALL_METRICS after hyperslab_structure after metric:", ALL_METRICS)
    print("region_param:", region_param)
    print("metric:", metric)
    print("scalar:", scalar)
    print("model:", model)
    query = db.session.query(Scalar)
    if region_param:
        query = query.filter(Scalar.region == region_param)
    if metric:
        query = query.filter(Scalar.metric.contains(metric))
    if scalar:
        query = query.filter(Scalar.scalar == scalar)
    if model:
        query = query.filter(Scalar.model == model)
    query.group_by(Scalar.metric, Scalar.model)
    output = query.all()
    scalar_schema = ScalarSchema(many=True)
    schema_output = scalar_schema.dump(output)
    for result in schema_output:
        # print("result:", result)
        result_region = result["region"]
        result_metric = result["metric"]
        result_scalar = result["scalar"]
        result_model = result["model"]
        result_value = result["value"]
        hyperslab_structure[result_region].setdefault(result_metric, {})
        hyperslab_structure[result_region][result_metric].setdefault(
            result_scalar, {})
        hyperslab_structure[result_region][result_metric][result_scalar].setdefault(
            result_model, result_value)
    return jsonify({'RESULTS': hyperslab_structure})
