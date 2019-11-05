from chalice import Chalice
from chalice import BadRequestError
import logging
from chalicelib import hyperslab_parse

app = Chalice(app_name='cmec_backend')
# Enable DEBUG logs.
app.log.setLevel(logging.DEBUG)


@app.route('/')
def index():
    return {'hello': 'world'}


@app.route('/hyperslab', methods=['POST'], content_types=['application/json'])
def hyperslab():
    app.log.debug("This is a debug statement")
    app.log.debug(app.current_request.json_body)
    data = app.current_request.json_body
    options = [data["region"], data["metric"],
               data["statistic"], data["model"]]
    app.log.debug(options)

    wildcards = options.count("*")
    app.log.debug(wildcards)
    if wildcards == 0:
        output_file = hyperslab_parse.extract_scalar(options)["file_name"]
    elif wildcards == 1:
        output_file = hyperslab_parse.extract_one_dimension(options, output_file=True)[
            "file_name"]
    elif wildcards == 2:
        output_file = hyperslab_parse.extract_two_dimension(options)[
            "file_name"]
    else:
        raise BadRequestError(
            "Invalid number of hyperslabs chosen. The maximum number of hyperslabs that can be selected is 2. '%s' hyperslabs were chosen in your request" % (wildcards))

    app.log.debug(output_file)
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
