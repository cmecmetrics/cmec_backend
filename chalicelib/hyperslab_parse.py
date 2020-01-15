import json
import os
import boto3
import itertools
import copy

s3 = boto3.client('s3')
BUCKET_NAME = "cmec-data"

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

DATA_DIRECTORY = "chalicelib/json_data_files"


def load_json_data():
    # load json object
    with open("test.json") as scalar_json:
        scalar_data = json.load(scalar_json)
    return scalar_data


def write_json_file(obj):
    with open("data_file.json", "w") as write_file:
        json.dump(obj, write_file)


def main():
    scalar_data = load_json_data()
    write_json_file(obj)


def all_combinations(scalar_data):
    output = []

    metric_catalogues = scalar_data.keys()
    metric_catalogues_list = list(metric_catalogues)

    regions = set(
        [
            x.split()[-1]
            for x in scalar_data[metric_catalogues_list[0]].keys()
            if x != "children"
        ]
    )

    regions = list(regions)

    scores = []
    for region in regions:
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
            for score in score_dict.keys():
                scores.append(score)
            # scores.append(list(score_dict.keys()))

            metrics = scalar_data[catalogue]["children"]
            if metrics:
                for metric, metric_data in metrics.items():
                    metric_child_obj = {}
                    metric_child_obj["metric"] = "{}:{}".format(
                        catalogue, metric)
                    metric_child_obj["scores"] = []
                    metric_score_dict = {
                        key.rsplit(" ", 1)[0]: value
                        for (key, value) in metric_data.items()
                        if key != "children" and region in key
                    }
                    for metric_score in metric_score_dict.keys():
                        scores.append(metric_score)

    # print("scores:", scores)
    output.append(regions)
    output.append(metric_catalogues_list)
    output.append(list(set(scores)))
    output.append(MODEL_NAMES)
    for sublist in output:
        sublist.append("*")
    # print("output:", output)

    # print("combos: \n")
    combos = list(itertools.product(*output))
    # print(list(itertools.product(*output)))
    filtered = [x for x in combos if 0 < x.count("*") < 3]
    # print("filtered:", filtered)
    return filtered


def extract_values(obj, key):
    """Recursively pull values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Return all matching values in an object."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append({k: v})
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results


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

    scalar_data["RESULTS"] = {region: {metric: {scalar: {model: output}}}}

    file_name = "{}_{}_{}_{}_scalar.json".format(region, metric, scalar, model)
    if output_file:
        file_name = file_name.replace(" ", "_")
        s3.upload_fileobj(
            file_name, BUCKET_NAME, file_name.split(".")[0])

    return {"data": {model: output}, "file_name": file_name}


def extract_one_dimension(options_array, hyperslab_data=None, output_file=False, upload=False, DATA_DIRECTORY="json_data_files"):
    region_option, metric_option, scalar_option, model_option = options_array
    if not hyperslab_data:
        with open("json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
            scalar_data = json.load(scalar_json)
    else:
        scalar_data = hyperslab_data

    scalar_data_copy = copy.deepcopy(hyperslab_data)

    json_structure = scalar_data["DIMENSIONS"]["json_structure"]

    if region_option == "*":
        keys = scalar_data["RESULTS"].keys()
        temp = {}
        for key in keys:
            temp[key] = {}
            metrics = [metric_name for metric_name in scalar_data["RESULTS"]
                       [key].keys() if metric_option in metric_name]
            for metric in metrics:
                temp[key][metric] = {}
                temp[key][metric] = {
                    scalar_option: extract_scalar(
                        [key, metric, scalar_option, model_option], hyperslab_data=scalar_data_copy)["data"]
                }
        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            "*", metric_option, scalar_option, model_option)
    if metric_option == "*":
        keys = scalar_data["RESULTS"][region_option].keys()
        temp = {region_option: {}}
        for key in keys:
            temp[region_option][key] = {
                scalar_option: extract_scalar(
                    [region_option, key, scalar_option, model_option], hyperslab_data=scalar_data_copy)["data"]
            }

        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            region_option, "*", scalar_option, model_option
        )

    if scalar_option == "*":
        keys = scalar_data["RESULTS"][region_option][metric_option].keys()
        metrics = [
            metric_name
            for metric_name in scalar_data["RESULTS"][region_option].keys()
            if metric_option in metric_name
        ]
        temp = {region_option: {}}
        for metric in metrics:
            temp[region_option][metric] = {}
            for key in keys:
                temp[region_option][metric][key] = extract_scalar(
                    [region_option, metric, key, model_option], hyperslab_data=scalar_data_copy)["data"]
        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            region_option, metric_option, "*", model_option
        )
    if model_option == "*":
        temp = {region_option: {}}
        metrics = [
            metric_name
            for metric_name in scalar_data["RESULTS"][region_option].keys()
            if metric_option in metric_name
        ]
        for metric in metrics:
            try:
                keys = scalar_data["RESULTS"][region_option][metric][
                    scalar_option
                ].keys()
            except KeyError:
                keys = []
            temp[region_option][metric] = {scalar_option: {}}
            for key in keys:
                temp[region_option][metric][scalar_option][key] = extract_scalar(
                    [region_option, metric, scalar_option,
                        key], hyperslab_data=scalar_data
                )["data"].get(key)
        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            region_option, metric_option, scalar_option, "*"
        )

    if output_file:
        with open(os.path.join(DATA_DIRECTORY, file_name), "w") as write_file:
            json.dump(scalar_data, write_file, sort_keys=True)

    if upload:
        scalar_data_json = json.dumps(scalar_data, ensure_ascii=False)

        s3_resource = boto3.resource('s3')
        file_name = file_name.replace(" ", "_")
        s3 = boto3.resource('s3').Object(
            BUCKET_NAME, file_name).put(Body=scalar_data_json)
        # s3.upload_fileobj(
        #     temp, BUCKET_NAME, file_name.split(".")[0])

    return {"data": temp, "file_name": file_name}


def extract_two_dimension(options_array, hyperslab_data=None, output_file=False, upload=False, DATA_DIRECTORY="json_data_files"):
    region_option, metric_option, scalar_option, model_option = options_array
    if not hyperslab_data:
        with open("json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
            scalar_data = json.load(scalar_json)
    else:
        scalar_data = hyperslab_data

    scalar_data_copy = copy.deepcopy(hyperslab_data)
    print("extract two dimension called.")

    json_structure = scalar_data["DIMENSIONS"]["json_structure"]

    if region_option == "*":
        regions = scalar_data["RESULTS"].keys()
        for region in regions:
            key_output = extract_one_dimension(
                [region, metric_option, scalar_option, model_option], hyperslab_data=scalar_data_copy)["data"]
            scalar_data["RESULTS"][region] = key_output[region]

        file_name = "{}_{}_{}_{}_scalar.json".format(
            "*", metric_option, scalar_option, model_option)
    elif metric_option == "*":
        metrics = scalar_data["RESULTS"][region_option].keys()
        temp = {region_option: {}}
        for metric in metrics:
            key_output = extract_one_dimension(
                [region_option, metric, scalar_option,
                    model_option], hyperslab_data=scalar_data_copy
            )["data"]
            temp[region_option][metric] = key_output[region_option][metric]

        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            region_option, "*", scalar_option, model_option
        )
    elif scalar_option == "*":
        temp = {region_option: {}}
        metrics = [
            metric_name
            for metric_name in scalar_data["RESULTS"][region_option].keys()
            if metric_option in metric_name
        ]
        for metric in metrics:
            temp[region_option][metric] = {}
            keys = scalar_data["RESULTS"][region_option][metric].keys()
            print("metric:", metric)
            for key in keys:
                print("key:", key)
                try:
                    key_output = extract_one_dimension(
                        [region_option, metric, key,
                            model_option], hyperslab_data=scalar_data_copy
                    )["data"]
                except TypeError:
                    print("region_option:", region_option)
                    print("metric:", metric)
                    print("key:", key)
                    print("model_option:", model_option)
                    key_output = extract_one_dimension(
                        [region_option, metric, key,
                            model_option], hyperslab_data=scalar_data_copy
                    )
                    print("key_output:", key_output)
                    raise
                print("key_output:", key_output)
                temp[region_option][metric][key] = key_output[region_option][metric][key]

        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            region_option, metric_option, "*", model_option
        )
        # print("hyperslab file name:", file_name)
    if output_file:
        with open(os.path.join(DATA_DIRECTORY, file_name), "w") as write_file:
            json.dump(scalar_data, write_file, sort_keys=True)

    if upload:
        print("uploading file to S3 Bucket")
        scalar_data_json = json.dumps(scalar_data, ensure_ascii=False)
        s3_resource = boto3.resource('s3')
        file_name = file_name.replace(" ", "_")
        s3 = boto3.resource('s3').Object(
            BUCKET_NAME, file_name).put(Body=scalar_data_json)

    return {"data": temp, "file_name": file_name}


if __name__ == "__main__":
    # extract_scalar(
    #     ["global", "Ecosystem and Carbon Cycle", "Bias Score", "BCC-CSM2-MR"]
    # )

    # extract_one_dimension(
    #     ["*", "Ecosystem and Carbon Cycle", "Bias Score", "BCC-CSM2-MR"], output_file=True
    # )
    # output = extract_one_dimension(
    #     ["global", "*", "Bias Score", "BCC-CSM2-MR"], output_file=True
    # )
    # print("output:", output)
    # extract_one_dimension(
    #     ["global", "Ecosystem and Carbon Cycle", "*", "BCC-CSM2-MR"], output_file=True
    # )
    # extract_one_dimension(["global", "Ecosystem and Carbon Cycle", "Bias Score", "*"], output_file=True)
    # extract_two_dimension(["*", "*", "Bias Score", "BCC-CSM2-MR"], output_file=True)
    # extract_two_dimension(["global", "*", "*", "BCC-CSM2-MR"], output_file=True)
    # extract_two_dimension(
    #     ["global", "Ecosystem and Carbon Cycle", "*", "*"], output_file=True
    # )
    scalar_data = load_json_data()
    # # reformat_json_for_postgres(scalar_data)
    combos = all_combinations(scalar_data)

    with open("json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
        hyperslab_data = json.load(scalar_json)
    # output = extract_one_dimension(
    #     ["*", "Ecosystem and Carbon Cycle", 'Overall Score', 'bcc-csm1-1'])
    # print("output:", output)
    for index, combo in enumerate(combos):
        print("{}): {}".format(index, combo))
        if combo.count("*") == 1:
            # extract_one_dimension(
            #     combo, hyperslab_data=hyperslab_data, output_file=True, upload=True, DATA_DIRECTORY="json_data_files/Hyperslab_files")
            continue
        else:
            extract_two_dimension(
                combo, hyperslab_data=hyperslab_data, output_file=True, upload=True, DATA_DIRECTORY="json_data_files/Hyperslab_files")

    print("Upload completed")
