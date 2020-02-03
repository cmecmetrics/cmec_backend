import json
import logging
import os
from flask import Blueprint, render_template, current_app, request, jsonify, Response, make_response, send_file, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, MetaData, create_engine

from chalice import BadRequestError, Chalice, Response
from chalicelib import hyperslab_parse
from flask_cors import CORS
from cmec_backend.models import db, Scalar, ScalarSchema
import pprint


engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route("/hyperslab", methods=["POST"])
def test():
    json_output = {}
    data = request.json
    region, metric, scalar, model = [
        data["region"], data["metric"], data["scalar"], data["model"]]
    # print("options:")
    # print(options)
    print("region:", region)
    print("metric:", metric)
    # game_object = db.session.query(Game).filter(
    #     Game.game_key.contains(game_file)).first()
    query = db.session.query(Scalar)
    if region:
        query = query.filter(Scalar.region == region)
        json_output[region] = {}
    else:
        json_output["globe"] = {}
        json_output["global"] = {}
        json_output["southamericaamazon"] = {}
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
        json_output[result_region].setdefault(result_metric, {})
        json_output[result_region][result_metric].setdefault(
            result_scalar, {})
        json_output[result_region][result_metric][result_scalar].setdefault(
            result_model, result_value)
    # json_output[region] = schema_output
    return jsonify({'RESULTS': json_output})
    # output = db.session.query(Scalar).filter(
    #     Scalar.metric.contains(metric), Scalar.region == region).all()
    # output = Scalar.query.filter_by(
    #     Scalar.metric.contains(metric), Scalar.region=region).all()
    for record in output:
        pprint.pprint(record.__dict__)
    # print("output:", output)


# @bp.route("/hyperslab", methods=["POST"])
# def hyperslab():
#     print("This is a debug statement")
#     print("json_body:")
#     print(request.json)
#     data = request.json
#     options = [data["region"], data["metric"], data["scalar"], data["model"]]
#     print("options:")
#     print(options)

#     wildcards = options.count("*")
#     print(wildcards)
#     if wildcards == 0:
#         output_file = hyperslab_parse.extract_scalar(options)["file_name"]
#     elif wildcards == 1:
#         output_file = hyperslab_parse.extract_one_dimension(options, output_file=True)[
#             "file_name"
#         ]
#     elif wildcards == 2:
#         output_file = hyperslab_parse.extract_two_dimension(options, output_file=True)[
#             "file_name"
#         ]
#     else:
#         raise BadRequestError(
#             "Invalid number of hyperslabs chosen. The maximum number of hyperslabs that can be selected is 2. '%s' hyperslabs were chosen in your request"
#             % (wildcards)
#         )

#     # print(output_file)
#     # upload tmp file to s3 bucket
#     # s3_client.upload_file(output_file, "cmec-data", output_file)

#     # return Response(body='upload successful: {}'.format(output_file),
#     #                 status_code=200,
#     #                 headers={'Content-Type': 'text/plain'})
#     output_file_response = json.dumps(output_file)
#     return Response(output_file_response, status=200, mimetype="application/json")
