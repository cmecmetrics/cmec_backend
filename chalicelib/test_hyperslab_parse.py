import hyperslab_parse


def test_extract_one_dimension():
    output = hyperslab_parse.extract_one_dimension(
        ["global", "*", "Bias Score", "BCC-CSM2-MR"], output_file=True
    )
    print("output:", output)
    assert "global" in output["data"]
    assert "Ecosystem and Carbon Cycle" in output["data"]["global"]

    output = hyperslab_parse.extract_one_dimension(
        ["southamericaamazon", "*", "Bias Score", "BCC-CSM2-MR"], output_file=True
    )


def test_extract_two_dimension():
    # output = hyperslab_parse.extract_two_dimension(
    #     ["southamericaamazon", "Ecosystem and Carbon Cycle", "*", "*"], output_file=True
    # )
    # print("two dimension output:", output)
    # assert "southamericaamazon" in output["data"]
    # assert "Ecosystem and Carbon Cycle" in output["data"]["southamericaamazon"]

    # output = hyperslab_parse.extract_two_dimension(
    #     ["global", "Ecosystem and Carbon Cycle", "*", "*"], output_file=True
    # )
    # print("two dimension output:", output)
    # assert "global" in output["data"]
    # assert "Ecosystem and Carbon Cycle" in output["data"]["global"]

    output = hyperslab_parse.extract_two_dimension(
        ["*", "Ecosystem and Carbon Cycle", "Temporal Distribution Score", "*"], output_file=True
    )
    print("two dimension output:", output)
    assert "global" in output["data"]
    assert "Ecosystem and Carbon Cycle" in output["data"]["global"]
