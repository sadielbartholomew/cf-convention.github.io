#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import pprint

import numpy as np
import matplotlib.pyplot as plt


XML_STD_NAME_TAG_PATTERN = re.compile(r'<entry id=\"(.+)\">')


def get_std_names_via_file(std_name_xml_filename):
    all_std_names_per_version = []
    with open(std_name_xml_filename, 'rt') as std_name_xml_data:    
        for line in std_name_xml_data:
            full_pattern_result = XML_STD_NAME_TAG_PATTERN.search(line)
            if full_pattern_result:
                all_std_names_per_version.append(
                    full_pattern_result.group(1).rstrip('\n'))
    return all_std_names_per_version



def get_total_per_version(std_names_list):
    return len(std_names_list)



def extract_xml_by_version_from_std_name_dir(std_name_dir):
    """ Walk 'cf-convention.github.io/Data/cf-standard-names/' dir for XML. """
    all_xml_file_paths = {}
    for dir_name, _, file_list in os.walk(std_name_dir):
        if dir_name.endswith("src"):
            for filename in file_list:
                if filename.endswith(".xml"):
                    version = dir_name.split("/")[1]
                    all_xml_file_paths[version] = dir_name + "/" + filename
    return all_xml_file_paths


def get_all_std_names_per_version(root_dir):
    totals = {}
    xml_loc_per_version = extract_xml_by_version_from_std_name_dir(root_dir)
    for version, filename in xml_loc_per_version.items():
        totals[version] = get_total_per_version(
            get_std_names_via_file(filename))
    return totals


def make_plot(totals_figures):
    fig, (ax1, ax2) = plt.subplots(2)

    # Convert current to assumed latest version, for plotting as int:
    current_val = totals_figures["current"]
    del totals_figures["current"]
    totals_figures = {int(ver): total for ver, total in totals_figures.items()}
    highest_vesion = max(totals_figures.keys())
    assume_curernt_version = highest_vesion + 1
    totals_figures[assume_curernt_version] = current_val

    data = sorted(totals_figures.items())
    ax1.plot(*zip(*data), 'ko-')
    print(data)

    change_for_next_ver_data = {}
    for key, val in totals_figures.items():
        if key == 1:
            continue
        else:
            try:
                totals_pervious_ver = totals_figures[key - 1]
            except KeyError:
                try:
                    totals_pervious_ver = totals_figures[key - 2]
                except:
                    raise Exception("Too large version gap?")
            change_for_next_ver_data[key] = val - totals_pervious_ver

    change_data = sorted(change_for_next_ver_data.items())
    print(change_for_next_ver_data)
    ax2.plot(*zip(*change_data), 'r.-')

    ax1.set(title='Totals per version of Standard Names',
            ylabel='Numebr of Standard Names')
    ax2.set(xlabel='Version', ylabel='Numebr of Standard Names')

    plt.show()



totals_data = get_all_std_names_per_version('..')

# Raw/crude table of totals per version:
pprint.pprint(totals_data)

# Nicer in a plot:
make_plot(totals_data)
