from chalice import Chalice, Response
from chalice import BadRequestError
import logging
from chalicelib import hyperslab_parse
from flask_cors import CORS

# app = Chalice(app_name='cmec_backend')
from flask import Flask, request, jsonify, Response
import json
app = Flask(__name__)
cors = CORS(app)

# Enable DEBUG logs.
app.debug = True
# app.log.setLevel(logging.DEBUG)


@app.route('/')
def index():
    return {'hello': 'world'}


# @app.route('/hyperslab', methods=['POST'], content_types=['application/json'], cors=True)
@app.route('/hyperslab', methods=['POST'])
def hyperslab():
    print("This is a debug statement")
    print("json_body:")
    print(request.json)
    data = request.json
    options = [data["region"], data["metric"],
               data["scalar"], data["model"]]
    print("options:")
    print(options)

    wildcards = options.count("*")
    print(wildcards)
    if wildcards == 0:
        output_file = hyperslab_parse.extract_scalar(options)["file_name"]
    elif wildcards == 1:
        output_file = hyperslab_parse.extract_one_dimension(options, output_file=True)[
            "file_name"]
    elif wildcards == 2:
        output_file = hyperslab_parse.extract_two_dimension(options, output_file=True)[
            "file_name"]
    else:
        raise BadRequestError(
            "Invalid number of hyperslabs chosen. The maximum number of hyperslabs that can be selected is 2. '%s' hyperslabs were chosen in your request" % (wildcards))

    print(output_file)
    # upload tmp file to s3 bucket
    # s3_client.upload_file(output_file, "cmec-data", output_file)

    # return Response(body='upload successful: {}'.format(output_file),
    #                 status_code=200,
    #                 headers={'Content-Type': 'text/plain'})
    output_file_response = json.dumps(output_file)
    return Response(output_file_response,
                    status=200,  mimetype='application/json')

# def upload_to_s3(file_name):

#     # get raw body of PUT request
#     body = app.current_request.raw_body

#     # write body to tmp file
#     tmp_file_name = '/tmp/' + file_name
#     with open(tmp_file_name, 'wb') as tmp_file:
#         tmp_file.write(body)

#     # upload tmp file to s3 bucket
#     s3_client.upload_file(tmp_file_name, BUCKET, file_name)

#     return Response(body='upload successful: {}'.format(file_name),
#                     status_code=200,
#                     headers={'Content-Type': 'text/plain'})
# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
