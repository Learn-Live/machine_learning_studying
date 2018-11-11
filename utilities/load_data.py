# -*- coding: utf-8 -*-
r"""
    tool for load data from local files
"""


def load_data(input_fil=''):
    """

    :param input_fil: input file
    :return:
    """
    data = []
    try:
        with open(input_fil, 'r') as read_hdl:  # read_handle
            for idx, line_str in enumerate(read_hdl):
                print(idx, line_str.strip('\n'))
                line_arr = line_str.strip('\n').split(',')
                data.append(line_arr)

        # return 0  # no matter what, finally always be execute
    except FileNotFoundError as e:  # like 'if '
        print('e:', e)
    else:
        print('try successful.')
    finally:
        print('print finally')

    print('body')

    return data