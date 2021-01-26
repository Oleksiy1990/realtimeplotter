import JSONinterpreter
import pytest
import json

def test_JSONread__check_JSON():
    # Class JSONread function __check_JSON(str)
    myJSONreader = JSONinterpreter.JSONread()
    correct_message_dict1 = {
            "jsonrpc":"2.0",
            "method":"test",
            "params":{},
            "id":0
            }
    correct_message_dict2 = {
            "jsonrpc":"2.0",
            "method":"test",
            "params":{"a":1},
            "id":5
            }
    incorrect_message_dict1 = {
            "jsonrpc":"2.",
            "method":"test",
            "params":{},
            "id":0
            }
    incorrect_message_dict2 = {
            "jsonrpc":"2.0",
            "method":{},
            "params":{},
            "id":0
            }
    incorrect_message_dict3 = {
            "jsonrpc":"2.0",
            "method":"test",
            "params":"test",
            "id":0
            }
    assert myJSONreader._JSONread__check_JSON(json.dumps(correct_message_dict1)) == (True,correct_message_dict1)
    assert myJSONreader._JSONread__check_JSON(json.dumps(correct_message_dict2)) == (True,correct_message_dict2)
    assert myJSONreader._JSONread__check_JSON(json.dumps(incorrect_message_dict1)) == (False,None)
    assert myJSONreader._JSONread__check_JSON(json.dumps(incorrect_message_dict2)) == (False,None)
    assert myJSONreader._JSONread__check_JSON(json.dumps(incorrect_message_dict3)) == (False,None)

def test_JSONread__message_key_to_function_name():
    # Class JSONread function __message_key_to_function_name(str)
    myJSONreader = JSONinterpreter.JSONread()

    msg1 = "oneTwo"
    msg2 = "onetwo"
    msg3 = "oneTwoThree"
    msg4 = "one123"

    assert myJSONreader._JSONread__message_key_to_function_name(msg1) == "one_two"
    assert myJSONreader._JSONread__message_key_to_function_name(msg2) == "onetwo"
    assert myJSONreader._JSONread__message_key_to_function_name(msg3) == "one_two_three"
    assert myJSONreader._JSONread__message_key_to_function_name(msg4) == "one123"

def test_JSONread_parse_JSON_message():
    myJSONreader = JSONinterpreter.JSONread()

    message_doClear_y1 = {
        "jsonrpc": "2.0",
        "method": "doClear",
        "params": {"clearData": "all"},
        "id": 0
    }
    message_doClear_n1 = {
        "jsonrpc": "2.0",
        "method": "doClear",
        "params": {"wrongname": "all"},
        "id": 0
    }

    message_setConfig_y1 = {
        "jsonrpc": "2.0",
        "method": "setConfig",
        "params": {"setAxisLabels":["myfavx","myfavy"]},
        "id": 0
    }

    message_setConfig_y2 = {
        "jsonrpc": "2.0",
        "method": "setConfig",
        "params": {"setPlotTitle":"title"},
        "id": 0
    }

    message_setConfig_y3 = {
        "jsonrpc": "2.0",
        "method": "setConfig",
        "params": {"setPlotTitle": "title",
                   "setAxisLabels":["myfavx","myfavy"]},
        "id": 0
    }

    message_setConfig_n1 = {
        "jsonrpc": "2.0",
        "method": "setConfig",
        "params": "title",
        "id": 0
    }

    message_addData_y1 = {
        "jsonrpc": "2.0",
        "method": "addData",
        "params": {"dataPoint":{"curveNumber":1,
                                "xval":1e-5,
                                "yval":0.5,
                                "yerr":0.01}},
        "id": 0
    }


    message_doFit_y1 = {
        "jsonrpc": "2.0",
        "method": "doFit",
        "params": {"performFitting":""},
        "id": 0
    }
    message_doFit_y2 = {
        "jsonrpc": "2.0",
        "method": "doFit",
        "params": {"performFitting":"",
                    "setFitFunction":"sinusoidal",
                    "setCurveNumber":0,
                    "setCropLimits":[0,1e-3]},
        "id": 0
    }

    message_getFitResult_y1 = {
        "jsonrpc": "2.0",
        "method": "getFitResult",
        "params": {"curveNumber":1},
        "id": 0
        }
    message_getFitResult_n1 = {
        "jsonrpc": "2.0",
        "method": "getFitResult",
        "params": {"getcurve":1},
        "id": 0
        }
    
    assert myJSONreader.parse_JSON_message(json.dumps(message_doClear_y1)) == [("clear_data","all")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_doClear_n1)) == [("nofunction", "")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_setConfig_n1)) == [("nofunction", "")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_setConfig_y1)) == [("set_axis_labels",
                                                                                  ["myfavx","myfavy"])]
    assert myJSONreader.parse_JSON_message(json.dumps(message_setConfig_y2)) == [("set_plot_title",
                                                                                  "title")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_setConfig_y3)) == [("set_axis_labels",
                                                                                  ["myfavx","myfavy"]),
                                                                                  ("set_plot_title",
                                                                                  "title")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_addData_y1)) == [("plot_single_datapoint", {"curveNumber":1,
                                                                                            "xval":1e-5,
                                                                                            "yval":0.5,
                                                                                            "yerr":0.01})]
    assert myJSONreader.parse_JSON_message(json.dumps(message_doFit_y1)) == [("perform_fitting","")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_doFit_y2)) == [("set_fit_function", "sinusoidal"),
                                                                             ("set_curve_number", 0),
                                                                             ("set_crop_limits", [0.,1e-3]),
                                                                             ("perform_fitting", "")]
    assert myJSONreader.parse_JSON_message(json.dumps(message_getFitResult_y1)) == [("get_fit_result",1)]
    assert myJSONreader.parse_JSON_message(json.dumps(message_getFitResult_n1)) == [("nofunction","")]
