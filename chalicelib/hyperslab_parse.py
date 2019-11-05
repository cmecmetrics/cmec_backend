import json
import os

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
        print("region:", region)
        for catalogue in metric_catalogues:
            print("catalogue:", catalogue)
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
                    print("metric:", metric)
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


def extract_scalar(options_array, output_file=False):
    with open("chalicelib/json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
        scalar_data = json.load(scalar_json)

    try:
        output = scalar_data["RESULTS"][options_array[0]][options_array[1]][
            options_array[2]
        ][options_array[3]]
    except KeyError:
        output = -999

    scalar_data["RESULTS"] = {
        options_array[0]: {
            options_array[1]: {options_array[2]: {options_array[3]: output}}
        }
    }

    file_name = "{}_{}_{}_{}_scalar.json".format(
                options_array[0], options_array[1], options_array[2], options_array[3]
    )
    if output_file:
        with open(os.path.join(DATA_DIRECTORY, file_name), "w") as write_file:
            json.dump(scalar_data, write_file, sort_keys=True)

    return {"data": {options_array[3]: output}, "file_name": file_name}


def extract_one_dimension(options_array, output_file=False):
    with open("chalicelib/json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
        scalar_data = json.load(scalar_json)

    json_structure = scalar_data["DIMENSIONS"]["json_structure"]

    if options_array[0] == "*":
        keys = scalar_data["RESULTS"].keys()
        for key in keys:
            metrics = [
                metric_name
                for metric_name in scalar_data["RESULTS"][key].keys()
                if options_array[1] in metric_name
            ]
            for metric in metrics:
                scalar_data["RESULTS"][key][metric] = {}
                scalar_data["RESULTS"][key][metric] = {
                    options_array[2]: extract_scalar(
                        [key, metric, options_array[2], options_array[3]]
                    )["data"]
                }
        file_name = "{}_{}_{}_{}_scalar.json".format(
            "all", options_array[1], options_array[2], options_array[3]
        )
    if options_array[1] == "*":
        keys = scalar_data["RESULTS"][options_array[0]].keys()
        temp = {options_array[0]: {}}
        for key in keys:
            temp[options_array[0]][key] = {
                options_array[2]: extract_scalar(
                    [options_array[0], key, options_array[2], options_array[3]]
                )["data"]
            }

        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            options_array[0], "all", options_array[2], options_array[3]
        )

    if options_array[2] == "*":
        keys = scalar_data["RESULTS"][options_array[0]
                                      ][options_array[1]].keys()
        metrics = [
            metric_name
            for metric_name in scalar_data["RESULTS"][options_array[0]].keys()
            if options_array[1] in metric_name
        ]
        temp = {options_array[0]: {}}
        for metric in metrics:
            temp[options_array[0]][metric] = {}
            for key in keys:
                temp[options_array[0]][metric][key] = extract_scalar(
                    [
                        options_array[0],
                        metric,
                        key,
                        options_array[3],
                    ]
                )["data"]
        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            options_array[0], options_array[1], "all", options_array[3]
        )
    if options_array[3] == "*":
        temp = {options_array[0]: {}}
        metrics = [
            metric_name
            for metric_name in scalar_data["RESULTS"][options_array[0]].keys()
            if options_array[1] in metric_name
        ]
        for metric in metrics:
            try:
                keys = scalar_data["RESULTS"][options_array[0]][metric][
                    options_array[2]
                ].keys()
            except KeyError:
                keys = []
            temp[options_array[0]][metric] = {options_array[2]: {}}
            for key in keys:
                temp[options_array[0]][metric][options_array[2]][key] = extract_scalar(
                    [options_array[0], metric, options_array[2], key]
                )["data"].get(key)
        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            options_array[0], options_array[1], options_array[2], "all"
        )

    if output_file:
        with open(os.path.join(DATA_DIRECTORY, file_name), "w") as write_file:
            json.dump(scalar_data, write_file, sort_keys=True)

    return {"data": temp, "file_name": file_name}


def extract_two_dimension(options_array, output_file=False):
    with open("chalicelib/json_data_files/ilamb_data_hyperslab_format.json") as scalar_json:
        scalar_data = json.load(scalar_json)

    json_structure = scalar_data["DIMENSIONS"]["json_structure"]

    if options_array[0] == "*":
        keys = scalar_data["RESULTS"].keys()
        for key in keys:
            key_output = extract_one_dimension(
                [key, options_array[1], options_array[2], options_array[3]]
            )["data"]
            scalar_data["RESULTS"][key] = key_output[key]

        file_name = "{}_{}_{}_{}_scalar.json".format(
            "all", options_array[1], options_array[2], options_array[3]
        )
    elif options_array[1] == "*":
        keys = scalar_data["RESULTS"][options_array[0]].keys()
        temp = {options_array[0]: {}}
        for key in keys:
            key_output = extract_one_dimension(
                [options_array[0], key, options_array[2], options_array[3]]
            )["data"]
            temp[options_array[0]][key] = key_output[options_array[0]][key]

        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            options_array[0], "all", options_array[2], options_array[3]
        )
    elif options_array[2] == "*":
        temp = {options_array[0]: {}}
        metrics = [
            metric_name
            for metric_name in scalar_data["RESULTS"][options_array[0]].keys()
            if options_array[1] in metric_name
        ]
        for metric in metrics:
            print("metric:", metric)
            temp[options_array[0]][metric] = {}
            keys = scalar_data["RESULTS"][options_array[0]][metric].keys()
            for key in keys:
                print("key:", key)
                key_output = extract_one_dimension(
                    [options_array[0], metric, key, options_array[3]]
                )["data"]
                print("key_output:", key_output)
                temp[options_array[0]][metric][key] = key_output[options_array[0]][
                    metric
                ][key]

        scalar_data["RESULTS"] = temp
        file_name = "{}_{}_{}_{}_scalar.json".format(
            options_array[0], options_array[1], "all", options_array[3]
        )
    if output_file:
        with open(os.path.join(DATA_DIRECTORY, file_name), "w") as write_file:
            json.dump(scalar_data, write_file, sort_keys=True)

        return {"data": temp, "file_name": file_name}


if __name__ == "__main__":
    # extract_scalar(
    #     ["global", "Ecosystem and Carbon Cycle", "Bias Score", "BCC-CSM2-MR"]
    # )

    # extract_one_dimension(
    #     ["*", "Ecosystem and Carbon Cycle", "Bias Score", "BCC-CSM2-MR"]
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
    extract_two_dimension(
        ["global", "Ecosystem and Carbon Cycle", "*", "*"], output_file=True
    )
