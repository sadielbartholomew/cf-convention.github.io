#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import pprint

from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as dates

XML_STD_NAME_TAG_PATTERN = re.compile(r'<entry id=\"(.+)\">')
XML_LAST_MODIFIED_PATTERN = re.compile(
    r'<last_modified>(.+)T(.+)</last_modified>')


def get_from_file(pattern, std_name_xml_filename):
    extracted_data = []
    with open(std_name_xml_filename, 'rt') as std_name_xml_data:    
        for line in std_name_xml_data:
            full_pattern_result = pattern.search(line)
            if full_pattern_result:
                extracted_data.append(
                    full_pattern_result.group(1).rstrip('\n'))
    return extracted_data


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


def get_all_std_names_per_version(root_dir, return_names=False):
    totals = {}
    names = {}
    xml_loc_per_version = extract_xml_by_version_from_std_name_dir(root_dir)
    for version, filename in xml_loc_per_version.items():
        names_in_version = get_from_file(XML_STD_NAME_TAG_PATTERN, filename)
        total = get_total_per_version(names_in_version)
        if not return_names:
            try:
                date = get_from_file(XML_LAST_MODIFIED_PATTERN, filename)[0]
            except:
                #raise Exception("Can't find date")
                date = "2000-01-01"  # USE AS PLOTTABLE PLACEHOLDER FOR NOW
            totals[version] = {"total": total, "date": date}
        else:
            names[version] = names_in_version
    if return_names:
        return names
    return totals


def get_new_names(all_std_names_per_version, newer_version, older_version,
                  print_on=False):
    newer_set = set(all_std_names_per_version[str(newer_version)])
    older_set = set(all_std_names_per_version[str(older_version)])
    difference = list(newer_set.difference(older_set))

    if print_on:
        print("new:")
        pprint.pprint(newer_set)
        print("\n\nold:")
        pprint.pprint(newer_set)
        print("\n\nadded since older:")
        pprint.pprint(difference)

    return difference


def make_plot_against_versions(totals_figures):
    # PLOT BY VERSION:
    fig, (ax1, ax2) = plt.subplots(2)

    # Convert current to assumed latest version, for plotting version as int:
    current_val = totals_figures["current"]
    totals_by_version = {int(ver): data["total"] for ver, data in
                         totals_figures.items() if ver != "current"}
    highest_vesion = max(totals_by_version.keys())
    assume_curernt_version = highest_vesion + 1
    totals_by_version[assume_curernt_version] = current_val["total"]

    data = sorted(totals_by_version.items())
    ax1.plot(*zip(*data), 'ko-')

    change_for_next_ver_data = {}
    for key, val in totals_by_version.items():
        if key == 1:
            continue
        else:
            try:
                totals_pervious_ver = totals_by_version[key - 1]
            except KeyError:
                try:
                    totals_pervious_ver = totals_by_version[key - 2]
                except:
                    raise Exception("Version gap too large?")
            change_for_next_ver_data[key] = val - totals_pervious_ver

    change_data = sorted(change_for_next_ver_data.items())

    ax2.plot(*zip(*change_data), 'r.-')

    ax1.set(title='Totals per version of Standard Names',
            ylabel='Numebr of Standard Names')
    ax2.set(xlabel='Version', ylabel='Numebr of Standard Names')

    plt.show()


def make_plot_against_dates(totals_figures):
    """ PLOT (SEPARATELY) BY DATE """
    fig_2, ax1_2 = plt.subplots()

    # Version 23 date issue, remove extra character that shouldn't be there:
    date_v23 = totals_figures["23"]["date"]
    totals_figures["23"]["date"] = date_v23.strip(":")

    totals_by_date = {
        datetime.strptime(data["date"], "%Y-%m-%d"): data["total"] for
        ver, data in totals_figures.items()}

    date_data = sorted(totals_by_date.items())

    ax1_2.plot(*zip(*date_data), 'ko-')
    ax1_2.set(
        title='Totals by date (at by-version resolution) of Standard Names',
        ylabel='Numebr of Standard Names'
    )
    plt.show()


def convert_underscored_phrase_to_words(all_names_list):
    name_phrase_list = []
    for name in all_names_list:
        phrase = name.replace("_", " ")
        name_phrase_list.append(phrase)
    return name_phrase_list


totals_data = get_all_std_names_per_version('..')

# Raw/crude table of totals per version:
pprint.pprint(totals_data)
# Nicer in a plot though, see final ilnes (plots block so leave until end)

# Inspect and print name differences as list to pass to online visualiser:
# Choose only two to insepct, those at the 'spikes':
v12_new_names = get_new_names(
    get_all_std_names_per_version('..', return_names=True),
    12, 11
)
print("\n\n\n", "-" * 15, "v12",  "-" * 15, "\n\n\n")
for sname in convert_underscored_phrase_to_words(v12_new_names):
    print(sname)

v49_new_names = get_new_names(
    get_all_std_names_per_version('..', return_names=True),
    49, 48
)
print("\n\n\n", "-" * 15, "v49",  "-" * 15, "\n\n\n")
for sname in convert_underscored_phrase_to_words(v49_new_names):
    print(sname)

# Nicer in a plot:
make_plot_against_versions(totals_data)
make_plot_against_dates(totals_data)
