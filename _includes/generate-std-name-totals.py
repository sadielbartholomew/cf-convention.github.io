#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import matplotlib.dates as dates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, ScalarFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
import os
import pprint
import re


# Run from root repo dir (or if from 'includes' dir, add initial ".."):
STD_NAME_ROOT_DIR_RELATIVE_PATH = os.path.join("Data", "cf-standard-names")


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
    for dir_path, _, file_list in os.walk(std_name_dir):
        if dir_path.endswith("src"):
            for filename in file_list:
                if filename.endswith(".xml"):
                    version = dir_path.split("/")[-2]
                    all_xml_file_paths[version] = dir_path + "/" + filename
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
                # No timestamp on v1, so assume from v1.0 of CF, Oct 2003 (see
                # http://cfconventions.org/faq.html#when_started)
                date = "2003-10-01"
            totals[version] = {"total": total, "date": date}
        else:
            names[version] = names_in_version
    if return_names:
        return names
    return totals


def calculate_difference_totals(totals_data):
    totals_with_diff_data = dict(totals_data)  # copy taking care with mutables
    totals_with_diff_data[1].update({"diff": 0})
    for ver, data in totals_data.items():
        if ver == 1:
            continue
        else:
            try:
                previous_ver_data = totals_data[ver - 1]
            except KeyError:  # rarely version is missing, but not >1 together
                previous_ver_data = totals_data[ver - 2]
            totals_with_diff_data[ver].update(
                {"diff": data["total"] - previous_ver_data["total"]})
    return totals_with_diff_data


def process_current(totals_figures):
    # Convert versions to integers for plotting:
    current_data = totals_figures["current"]
    totals_figures = {int(ver): data for ver, data in
                      totals_figures.items() if ver != "current"}
    # Convert current to assumed latest version, for plotting version as int:
    highest_vesion = max(totals_figures.keys())
    assume_current_version = highest_vesion + 1
    totals_figures[assume_current_version] = current_data
    return totals_figures


def pre_process(all_totals_data):
    """ Any processing on the raw data required pre-plot. """
    # Convert 'current' to latest version number (assumed)
    all_totals_data = process_current(all_totals_data)

    # Convert version strings to integers so they become plotable
    all_totals_data = {int(ver): data for ver, data in
                       all_totals_data.items()}

    # Version 23 date issue, remove extra character that shouldn't be there:
    date_v23 = all_totals_data[23]["date"]
    all_totals_data[23]["date"] = date_v23.strip(":")

    # Get diffs:
    all_totals_data = calculate_difference_totals(all_totals_data)

    return all_totals_data


def convert_date_str(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def make_raw_and_difference_plot(totals_figures, by_date=True):
    LINEWIDTH = 3
    
    totals_figures = pre_process(totals_figures)
    totals_figures = calculate_difference_totals(totals_figures)

    totals = {}
    diffs = {}
    for ver, data in totals_figures.items():
        if by_date:
            totals[convert_date_str(data["date"])] = data["total"]
            diffs[convert_date_str(data["date"])] = data["diff"]
        else:
            totals[ver] = data["total"]
            diffs[ver] = data["diff"]
    pprint.pprint(totals)  ### DEBUG

    sorted_totals = sorted(totals.items())
    sorted_diffs = sorted(diffs.items())

    plt.rcParams.update({'font.size': 12})
    #fig, (ax1, ax2) = plt.subplots(2)
    fig, ax1 = plt.subplots()
    ax1.set_title(
        'Number of standard names in the CF conventions table by date',
        fontsize=18
    )
    # Remove horizontal space between axes
    fig.subplots_adjust(hspace=0)
    ax1.set_xlabel(
        "Date of table version (marked at Jan 1st)",
        fontsize=14
    )
    ax1.tick_params(axis='x', which='minor')
    ax1.set_ylabel(
        "Total number",
        fontsize=14
    )
    ax1.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax2 = ax1.twinx()
    ax2.set_ylabel(
        "Difference in total number \nrelative to previous version",
        fontsize=14,
        rotation=270,
        labelpad=35
    )
    ax2.yaxis.set_minor_locator(AutoMinorLocator(2))


    axins1 = inset_axes(ax1, width="70%", height="33%", loc="upper left")
    axins1.yaxis.tick_right()

    axins2 = inset_axes(
        ax1, width="50%", height="30%", loc="lower right", borderpad=3)
    
    ax1.step(*zip(*sorted_totals), where='post',
             linestyle='-', color='crimson', alpha=0.4,
             linewidth=LINEWIDTH, zorder=2)

    st, = ax1.plot(
        *zip(*sorted_totals),
        marker=None, linestyle='dashed', color='crimson',
        linewidth=LINEWIDTH)
    ax1.yaxis.label.set_color(st.get_color())
    ax1.set_ylim(0, 4500)

    axins2.step(*zip(*sorted_totals), where='post',
             linestyle='-', color='crimson', alpha=0.4, linewidth=LINEWIDTH)

    axins2.plot(
        *zip(*sorted_totals),
        marker=None, linestyle='dashed', color='crimson',
        linewidth=LINEWIDTH)
    axins2.set_xlim(datetime(2019, 1, 1, 0, 0), datetime.now())
    axins2.set_ylim(4300, 4420)
    axins2.set_yticklabels([])
    axins2.set_xticklabels([])
    mark_inset(ax1, axins2, loc1=2, loc2=4, fc="none", ec="0.5")

    ax2.set_zorder(3)
    dt = ax2.stem(
        *zip(*sorted_diffs), use_line_collection=True, bottom=0)
    print(dt.markerline.__dict__)
    ax2.yaxis.label.set_color('C0')  # default matplotlib blue now

    ax1.tick_params(axis='y', colors=st.get_color())
    ax2.tick_params(axis='y', colors='C0')

    
    ax2.set_ylim(1, 1400)
    #ax2.plot(*zip(*sorted_diffs), 'r.-')

    axins1.plot(*zip(*sorted_diffs), marker='o', linestyle='None')  # needs string!
    axins1.set_ylim(1, 1500)
    axins1.set_yticks([1, 10, 100, 1000])
    axins1.set_yscale('log')
    axins1.yaxis.set_major_formatter(ScalarFormatter())


    axins1.set_xlim(datetime(2006, 9, 26, 0, 0))

    axins1.plot()  # fix zorder, when can't use on stem?
    ###fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()


def make_plot_against_dates(totals_figures):
    make_raw_and_difference_plot(totals_figures)


def make_plot_against_versions(totals_figures):
    make_raw_and_difference_plot(totals_figures, by_date=False)


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


def convert_underscored_phrase_to_words(all_names_list):
    name_phrase_list = []
    for name in all_names_list:
        phrase = name.replace("_", " ")
        name_phrase_list.append(phrase)
    return name_phrase_list


def print_version_comparison(newer_version, older_version):
    new_names = get_new_names(
        get_all_std_names_per_version(
            STD_NAME_ROOT_DIR_RELATIVE_PATH, return_names=True),
        newer_version, older_version
    )
    print("\n\n\n", "-" * 15, "New to v%s" % str(newer_version),
          "-" * 15, "\n\n\n")
    for sname in convert_underscored_phrase_to_words(new_names):
        print(sname)


# Inspect & print name differences as list to pass to online vis tool:
###print_version_comparison(12, 11)
###print_version_comparison(49, 48)

totals_data = get_all_std_names_per_version(STD_NAME_ROOT_DIR_RELATIVE_PATH)

# Raw/crude table of totals per version:
###pprint.pprint(totals_data)

# Nicer in a plot:
###make_plot_against_versions(totals_data)
make_plot_against_dates(totals_data)
