#!/usr/bin/python

import pickle
import copy
import json
import my_modules .my_tracing as debugging


@debugging .trace
def read_from_file (case, context):
    with open (context + '/' + context + '_' + case + '_' + 'pickle_dump', "rb") as f:
        debugging .log("Reading of file is in progress")
        return pickle .load (f)

@debugging .trace
def read_from_file_basic (directory = '', fname = ''):
    if  fname == '':
        debugging .log ("No filename given")
        raise Exception ('No filename given to read')

    full_fname = '/'.join ([directory, fname])
    with open (full_fname, "rb") as f:
        debugging .log("Reading of file", full_fname, "is in progress")
        return pickle .load (f)

@debugging .trace
def pickle_load (fname = ''):
    if  fname == '':
        debugging .log ("No filename given")
        raise Exception ('No filename given to read')

    with open (fname, "rb") as f:
        debugging .log ("Reading of file", fname, "is in progress")
        ret = pickle .load (f)
        debugging .log ("Loading complete")
        return ret

@debugging .trace 
def pickle_dump (obj, filename):
    debugging .log ("Opening file", filename)
    with open (filename, "wb") as fp:
        debugging .log ("Writing in file", filename)
        pickle .dump (obj, fp, pickle .HIGHEST_PROTOCOL)
        debugging .log ("writing complete")

@debugging .trace
def deep_copy (val):
    return copy .deepcopy(val)

@debugging .trace
def load_json_config (conf = ''):
    if conf == '' :
        debugging .log ("No configuration filename given")
        raise Exception ("No configuration filename given")

    with open (conf) as fp:
        ret = json .load (fp)
    debugging .log ("Loaded configuration for", ret ["full_name"])
    return ret

