import json
import os
import boto3
import itertools
import copy
from cmec_backend.models import db, Scalar
from flask import current_app
from sqlalchemy import Table, MetaData, create_engine

MODEL_NAMES = [
    "bcc-csm1-1",
    "bcc-csm1-1-m",
    "CESM1-BGC",
    "GFDL-ESM2G",
    "inmcm4",
    "IPSL-CM5A-LR",
    "MIROC-ESM",
    "MPI-ESM-LR",
    "NorESM1-ME",
    "MeanCMIP5",
    "BCC-CSM2-MR",
    "BCC-ESM1",
    "CESM2",
    "CESM2-WACCM",
    "CNRM-CM6-1",
    "CNRM-ESM2-1",
    "E3SMv1-CTC",
    "GISS-E2-1-G",
    "GISS-E2-1-H",
    "IPSL-CM6A-LR",
    "MIROC6",
    "MRI-ESM2-0",
    "MeanCMIP6",
]

DATA_DIRECTORY = "cmec_backend/static"


def load_json_data(json_file="test.json"):
    # load json object
    with open(json_file) as scalar_json:
        scalar_data = json.load(scalar_json)
    return scalar_data


def reformat_json_for_postgres(scalar_data):
    """
        Reformat ILAMB JSON file to format proposed by Paul for hyperslab extraction
    """
    output = {}

    output["DIMENSIONS"] = {
        "json_structure": ["region", "metric", "statistic", "model"]
    }
    output["RESULTS"] = []

    metric_catalogues = scalar_data.keys()
    metric_catalogues_list = list(metric_catalogues)
    regions = set(
        [
            x.split()[-1]
            for x in scalar_data[metric_catalogues_list[0]].keys()
            if x != "children"
        ]
    )

    for region in regions:
        obj = {}
        obj["region"] = region
        obj["metrics"] = []
        for catalogue in metric_catalogues:
            print("catalogue:", catalogue)
            metric_obj = {}
            metric_obj["metric"] = catalogue
            metric_obj["scores"] = []
            score_dict = {
                key.rsplit(" ", 1)[0]: value
                for (key, value) in scalar_data[catalogue].items()
                if key != "children" and region in key
            }
            for score, values in score_dict.items():
                score_obj = {score: score}
                model_scores = []
                for (key, value) in zip(MODEL_NAMES, values):
                    model_scores.append({"model": key, "score": value})
                score_obj["models"] = model_scores
                metric_obj["scores"].append(score_obj)
            obj["metrics"].append(metric_obj)

            metrics = scalar_data[catalogue]["children"]
            if metrics:
                for metric, metric_data in metrics.items():
                    print("metric:", metric)
                    metric_child_obj = {}
                    metric_child_obj["metric"] = "{}:{}".format(
                        catalogue, metric)
                    metric_child_obj["scores"] = []
                    metric_score_dict = {
                        key.rsplit(" ", 1)[0]: value
                        for (key, value) in metric_data.items()
                        if key != "children" and region in key
                    }
                    for score, values in metric_score_dict.items():
                        metric_child_score_obj = {score: score}
                        metric_child_model_scores = []
                        for (key, value) in zip(MODEL_NAMES, values):
                            metric_child_model_scores.append(
                                {"model": key, "score": value})
                        metric_child_score_obj["models"] = metric_child_model_scores
                        metric_child_obj["scores"].append(
                            metric_child_score_obj)

                    obj["metrics"].append(metric_child_obj)

                    observational_products = metric_data["children"]
                    if observational_products:
                        for product, product_value in observational_products.items():
                            print("product:", product)
                            product_obj = {}
                            product_obj["metric"] = "{}:{}:{}".format(
                                catalogue, metric, product)
                            product_obj["scores"] = []
                            product_score_dict = {
                                key.rsplit(" ", 1)[0]: value
                                for (key, value) in product_value.items()
                                if key != "children" and region in key
                            }
                            for score, values in product_score_dict.items():
                                product_score_obj = {score: score}
                                product_model_scores = []
                                for (key, value) in zip(MODEL_NAMES, values):
                                    product_model_scores.append(
                                        {"model": key, "score": value})
                                product_score_obj["models"] = product_model_scores
                                product_obj["scores"].append(product_score_obj)

                            obj["metrics"].append(product_obj)

        output["RESULTS"].append(obj)

    with open("json_data_files/postgres_json_format.json", "w") as write_file:
        json.dump(output, write_file, sort_keys=True)


def reformat_json_for_hyperslabs(scalar_data):
    """
        Reformat ILAMB JSON file to format proposed by Paul for hyperslab extraction
    """
    output = {}

    output["DIMENSIONS"] = {
        "json_structure": ["region", "metric", "statistic", "model"]
    }
    output["RESULTS"] = {}

    metric_catalogues = scalar_data.keys()
    metric_catalogues_list = list(metric_catalogues)
    regions = set(
        [
            x.split()[-1]
            for x in scalar_data[metric_catalogues_list[0]].keys()
            if x != "children"
        ]
    )

    obj = {}
    for region in regions:
        obj[region] = {}
        # print("region:", region)
        for catalogue in metric_catalogues:
            # print("catalogue:", catalogue)
            score_dict = {
                key.rsplit(" ", 1)[0]: value
                for (key, value) in scalar_data[catalogue].items()
                if key != "children" and region in key
            }
            for score, values in score_dict.items():
                score_dict[score] = {
                    key: value for (key, value) in zip(MODEL_NAMES, values)
                }
            # print("score_dict:", score_dict)
            obj[region][catalogue] = score_dict
            metrics = scalar_data[catalogue]["children"]
            if metrics:
                for metric, value in metrics.items():
                    # print("metric:", metric)
                    metric_score_dict = {
                        key.rsplit(" ", 1)[0]: value
                        for (key, value) in value.items()
                        if key != "children" and region in key
                    }
                    for score, values in metric_score_dict.items():
                        metric_score_dict[score] = {
                            key: value for (key, value) in zip(MODEL_NAMES, values)
                        }
                    # print("metric_score_dict:", metric_score_dict)
                    obj[region]["{}::{}".format(
                        catalogue, metric)] = metric_score_dict
                    observational_products = value["children"]
                    if observational_products:
                        for product, product_value in observational_products.items():
                            product_score_dict = {
                                key.rsplit(" ", 1)[0]: value
                                for (key, value) in product_value.items()
                                if key != "children" and region in key
                            }
                            for score, values in product_score_dict.items():
                                product_score_dict[score] = {
                                    key: value
                                    for (key, value) in zip(MODEL_NAMES, values)
                                }
                            # print("product:", product)
                            # print("product_score_dict:", product_score_dict)
                            obj[region][
                                "{}::{}::{}".format(catalogue, metric, product)
                            ] = product_score_dict

    output["RESULTS"] = obj

    with open("chalicelib/json_data_files/ilamb_data_hyperslab_format.json", "w") as write_file:
        json.dump(output, write_file, sort_keys=True)


def extract_scalar(options_array, hyperslab_data=None, output_file=False):
    region, metric, scalar, model = options_array
    if not hyperslab_data:
        with open("json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
            scalar_data = json.load(scalar_json)
    else:
        scalar_data = hyperslab_data

    try:
        output = scalar_data["RESULTS"][region][metric][scalar][model]
    except KeyError:
        output = -999

    return output
