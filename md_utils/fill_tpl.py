#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fills in a template evb/rmd parameter files
"""
import argparse
import os
import sys
from collections import OrderedDict

from md_utils.md_common import (InvalidDataError, GOOD_RET, INPUT_ERROR, warning, IO_ERROR, process_cfg, read_tpl,
                                create_out_fname, str_to_file, TemplateNotReadableError, MISSING_SEC_HEADER_ERR_MSG)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

# Constants #
TPL_FILE = 'tpl_file'
FILLED_TPL_FNAME = 'filled_tpl_name'
OUT_DIR = 'out_dir'

# Config File Sections
MAIN_SEC = 'main'
TPL_VALS_SEC = 'tpl_vals'
TPL_EQS_SEC = 'tpl_equations'
VALID_SEC_NAMES = [MAIN_SEC, TPL_VALS_SEC, TPL_EQS_SEC]

# for storing template values
TPL_VALS = 'parameter_values'
TPL_EQ_VALS = 'calculated_parameters'
MULT_VAL_LIST = 'list_params_with_multi_vals'


# Defaults
DEF_CFG_FILE = 'fill_tpl.ini'
DEF_TPL = 'fill_tpl.tpl'
DEF_CFG_VALS = {TPL_FILE: DEF_TPL, OUT_DIR: None, FILLED_TPL_FNAME: None,
                }
REQ_KEYS = {}


# Logic #

# CLI Processing #

def process_tpl_vals(raw_key_val_tuple_list, val_dict, multi_val_param_list):
    """
    In case there are multiple (comma-separated) values, split on comma and strip. Do not convert to int or float;
       that will be done later if needed for equations
    The program creates the val_dict and multi_val_param_list (fed in empty)

    @param raw_key_val_tuple_list: key-value dict read from configuration file
    @param val_dict: a dictionary of values (strings); check for commas to indicate multiple parameters
    @param multi_val_param_list: a list of the parameters which contain multiple values
    """
    for key, val in raw_key_val_tuple_list:
        val_dict[key] = [x.strip() for x in val.split(',')]
        if len(val_dict[key]) > 1:
            multi_val_param_list.append(key)


# def process_eq_vals(raw_key_val_dict, eq_dict):
#     """
#
#     @param raw_key_val_dict:
#     @param eq_dict:
#     @return:
#     """
#     # todo: read and process equations
#     pass


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    try:
        good_files = config.read(f_loc)
    except MissingSectionHeaderError:
        raise InvalidDataError(MISSING_SEC_HEADER_ERR_MSG.format(f_loc))
    if not good_files:
        raise IOError('Could not read file {}'.format(f_loc))

    # Start with empty template value dictionaries to be filled
    proc = {TPL_VALS: OrderedDict(), TPL_EQ_VALS: OrderedDict(), MULT_VAL_LIST: []}

    if MAIN_SEC not in config.sections():
        raise InvalidDataError("The configuration file is missing the required '{}' section".format(MAIN_SEC))

    for section in config.sections():
        if section == MAIN_SEC:
            try:
                proc.update(cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS))
            except InvalidDataError as e:
                if 'Unexpected key' in e.message:
                    raise InvalidDataError(e.message + " Does this belong \nin a template value section such as '[{}]'?"
                                                       "".format(TPL_VALS_SEC))
        elif section == TPL_VALS_SEC:
            process_tpl_vals(config.items(section), proc[TPL_VALS], proc[MULT_VAL_LIST])
        elif section == TPL_EQS_SEC:
            proc[TPL_EQ_VALS] = dict(config.items(section))
        else:
            raise InvalidDataError("Section name '{}' in not one of the valid section names: {}"
                                   "".format(section, VALID_SEC_NAMES))

    return proc


def parse_cmdline(argv=None):
    """
    Returns the parsed argument list and return code.
    :param argv: A list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Fills in a template evb file with parameter values.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    parser.add_argument("-f", "--filled_tpl_name", help="File name for new file to be created by filling the template "
                                                        "file. It can also be specified in the configuration file. "
                                                        "If specified in both places, the command line option will "
                                                        "take precedence.",
                        default=None)

    args = None
    try:
        args = parser.parse_args(argv)
        if not os.path.isfile(args.config[TPL_FILE]):
            if args.config[TPL_FILE] == DEF_TPL:
                error_message = "Check input for the configuration key '{}'; " \
                                "could not find the default template file: {}"
            else:
                error_message = "Could not find the template file specified with " \
                                "the configuration key '{}': {}"
            raise IOError(error_message.format(TPL_FILE, args.config[TPL_FILE]))
        if args.filled_tpl_name is not None:
            args.config[FILLED_TPL_FNAME] = args.filled_tpl_name
        if args.config[FILLED_TPL_FNAME] is None:
            raise InvalidDataError("Missing required key '{}', which can be specified in the "
                                   "required either in the command line for configuration file."
                                   "".format(FILLED_TPL_FNAME))
    except (KeyError, InvalidDataError, IOError, SystemExit) as e:
        if e.message == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR
    return args, GOOD_RET


def fill_save_tpl(cfg, tpl_str, tpl_vals_dict):
    """
    use the dictionary to make the file name and filled template. Then save the file.
    @param cfg: configuration for run
    @param tpl_str: the string to be filled to make the filled tpl file
    @param tpl_vals_dict: dictionary of tpl keys and vals
    """
    try:
        filled_tpl_str = tpl_str.format(**tpl_vals_dict)
    except KeyError as e:
        raise KeyError("Key '{}' not found in the configuration but required for template file: {}"
                       "".format(e.message, cfg[TPL_FILE]))

    try:
        filled_fname_str = cfg[FILLED_TPL_FNAME].format(**tpl_vals_dict)
    except KeyError as e:
        raise KeyError("Key '{}' not found in the configuration but required for filled template file name: {}"
                       "".format(e.message, cfg[FILLED_TPL_FNAME]))

    new_par_fname = create_out_fname(filled_fname_str, base_dir=cfg[OUT_DIR])
    str_to_file(filled_tpl_str, new_par_fname)


def make_tpl(cfg):
    """
    Combines the dictionary and template file to create the new file
    @param cfg:
    @return:
    """

    tpl_str = read_tpl(cfg[TPL_FILE])
    tpl_vals_dict = {}

    # first, populate the template with the first values of all value lists.
    for key, val_list in cfg[TPL_VALS].items():
        tpl_vals_dict[key] = val_list[0]
    for key, eq_tpl in cfg[TPL_EQ_VALS]:
        print(key, eq_tpl)
    fill_save_tpl(cfg, tpl_str, tpl_vals_dict)

    # then, for each key that has more than 1 value, print more!
    for key_id in cfg[MULT_VAL_LIST]:

        for val in cfg[TPL_VALS][key][1:]:
            tpl_vals_dict[key] = val
            fill_save_tpl(cfg, tpl_str, tpl_vals_dict)
    #     for val in cfg[TPL_VALS][key][1:]:
    #         print(val)
    #         # tpl_vals_dict[key] = val
    #         # for eq_key, eq_tpl in cfg[TPL_EQ_VALS].items():
    #         #     assert isinstance(eq_tpl, str)
    #         #     print(eq_key)
    #    fill_save_tpl(cfg, tpl_str, tpl_vals_dict)


def main(argv=None):
    """
    Runs the main program.

    :param argv: The command line arguments.
    :return: The return code for the program's termination.
    """
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config

    try:
        make_tpl(cfg)
    except (TemplateNotReadableError, IOError) as e:
        warning("Problems reading file: {}".format(e))
        return IO_ERROR
    except (KeyError, InvalidDataError) as e:
        warning(e)
        return IO_ERROR

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
