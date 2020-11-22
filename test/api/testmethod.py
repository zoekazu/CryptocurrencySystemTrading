import requests

# All function need to implement "assert"


def ck_perfect_match(api_func, case):
    if 'req' in case.keys():
        res = api_func(*case['req'].values())
    else:
        res = api_func()
    assert res == case['res']


def ck_res_status(res_status):
    assert requests.codes.ok == res_status


def ck_part_match(api_func, case):
    if 'req' in case.keys():
        res = api_func(*case['req'].values())
    else:
        res = api_func()
    assert case['res'] in res


def ck_apires_arch(api_func, case):
    if 'req' in case.keys():
        res = api_func(**case['req'])
    else:
        res = api_func()
    assert res
    ck_res_arch(res, case)


def ck_res_arch(res, case):
    case_res = case['res']

    # if the respose is list, test representative values
    if isinstance(res, list):
        res = res[0]
        case_res = case_res[0]

    res_keys = res.keys()
    assert res_keys == case_res.keys()
    for res_key in res_keys:
        assert isinstance(res[res_key], type(case_res[res_key]))

        # if the value of dict is list
        if isinstance(res[res_key], list):
            for res_ch, case_ch in zip(res[res_key], case_res[res_key]):
                assert isinstance(res_ch.values(), type(case_ch.values()))

        # if the value of dict is dict
        if isinstance(res[res_key], dict):
            assert res[res_key].values() == case_res[res_key].values()
