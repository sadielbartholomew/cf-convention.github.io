#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import numpy as np
import os
import pprint
import re

import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import (
    AutoMinorLocator, ScalarFormatter, LogLocator, NullFormatter
)
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

from wordcloud import WordCloud


# Must run this script from the root repo (else need to amend the below path):
STD_NAME_ROOT_DIR_RELATIVE_PATH = os.path.join("Data", "cf-standard-names")
VIS_DIR_LOCATION = os.path.join("_includes", "standard-names-vis")

XML_STD_NAME_TAG_PATTERN = re.compile(r'<entry id=\"(.+)\">')
XML_LAST_MODIFIED_PATTERN = re.compile(
    r'<last_modified>(.+)T(.+)</last_modified>')


def get_from_file(pattern, std_name_xml_filename):
    """TODO."""
    extracted_data = []
    with open(std_name_xml_filename, 'rt') as std_name_xml_data:
        for line in std_name_xml_data:
            full_pattern_result = pattern.search(line)
            if full_pattern_result:
                extracted_data.append(
                    full_pattern_result.group(1).rstrip('\n'))
    return extracted_data


def get_total_per_version(std_names_list):
    """TODO."""
    return len(std_names_list)


def extract_xml_by_version_from_std_name_dir(std_name_dir):
    """Walk 'cf-convention.github.io/Data/cf-standard-names/' dir for XML."""
    all_xml_file_paths = {}
    for dir_path, _, file_list in os.walk(std_name_dir):
        if dir_path.endswith("src"):
            for filename in file_list:
                if filename.endswith(".xml"):
                    version = dir_path.split("/")[-2]
                    all_xml_file_paths[version] = dir_path + "/" + filename
    return all_xml_file_paths


def get_all_std_names_per_version(root_dir, return_names=False):
    """TODO."""
    totals = {}
    names = {}
    xml_loc_per_version = extract_xml_by_version_from_std_name_dir(root_dir)
    for version, filename in xml_loc_per_version.items():
        names_in_version = get_from_file(XML_STD_NAME_TAG_PATTERN, filename)
        total = get_total_per_version(names_in_version)
        if not return_names:
            try:
                date = get_from_file(XML_LAST_MODIFIED_PATTERN, filename)[0]
            except IndexError:
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
    """TODO."""
    totals_with_diff_data = dict(totals_data)  # copy taking care with mutables
    totals_with_diff_data[1].update({"diff": 0})
    for ver, data in totals_data.items():
        if ver == 1:
            continue
        else:
            try:
                previous_ver_data = totals_data[ver - 1]
            except KeyError:  # account for case of v39 (v38 was skipped)
                previous_ver_data = totals_data[ver - 2]
            totals_with_diff_data[ver].update(
                {"diff": data["total"] - previous_ver_data["total"]})
    return totals_with_diff_data


def process_current(totals_figures):
    """TODO."""
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
    """Any processing on the raw data required pre-plot."""
    # Convert 'current' to latest version number (assumed)
    all_totals_data = process_current(all_totals_data)

    # Convert version strings to integers so they become plotable
    all_totals_data = {int(ver): data for ver, data in
                       all_totals_data.items()}

    # TODO: when update branch, can remove this as v23 date issue was resolved
    # Version 23 date issue, remove extra character that shouldn't be there:
    date_v23 = all_totals_data[23]["date"]
    all_totals_data[23]["date"] = date_v23.strip(":")

    # Get diffs:
    all_totals_data = calculate_difference_totals(all_totals_data)

    return all_totals_data


def convert_date_str(date_str):
    """TODO."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def make_raw_and_difference_plot(totals_figures, by_date=True):
    """TODO."""
    LINEWIDTH = 3

    # Get data for totals and diffs
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
    sorted_totals = sorted(totals.items())
    sorted_diffs = sorted(diffs.items())

    # Plot formatting & styling, on an axis-by-axis basis:
    # ...for the overall plot & figure:
    plt.rcParams.update({'font.size': 12})
    fig, ax1 = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(hspace=0)

    # ...for ax1:
    ax1.set_title(
        'Number of standard names in the CF conventions table by date',
        fontsize=18
    )
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
    ax1.step(*zip(*sorted_totals), where='post',
             linestyle='-', color='crimson', alpha=0.4,
             linewidth=LINEWIDTH, zorder=2)
    st, = ax1.plot(
        *zip(*sorted_totals),
        marker=None, linestyle='dashed', color='crimson',
        linewidth=LINEWIDTH)
    ax1.yaxis.label.set_color(st.get_color())
    ax1.set_ylim(0, 4500)
    ax1.tick_params(axis='y', colors=st.get_color())

    # ...for ax2:
    ax2 = ax1.twinx()
    ax2.set_ylabel(
        "Difference in total number \nrelative to previous version",
        fontsize=14,
        rotation=270,
        labelpad=35
    )
    ax2.yaxis.set_minor_locator(AutoMinorLocator(1))
    ax2.set_zorder(3)
    dt = ax2.stem(
        *zip(*sorted_diffs), use_line_collection=True, bottom=0)
    ax2.yaxis.label.set_color('C0')
    ax2.tick_params(axis='y', colors='C0')
    ax2.set_ylim(1, 1400)

    # ...for axins1 (the inset axis):
    axins1 = inset_axes(ax1, width="75%", height="33%", loc="upper left")
    axins1.yaxis.tick_right()
    # Note linestyle here must be a string of None not the type None!
    axins1.plot(*zip(*sorted_diffs), marker='o', linestyle='None')
    axins1.set_ylim(1, 1700)
    axins1.set_yscale('log')
    axins1.set_yticks([1, 10, 100, 1000])
    axins1.yaxis.set_major_formatter(ScalarFormatter())
    locmin = LogLocator(
        base=10.0, subs=np.arange(2, 10) * .1, numticks=100)
    axins1.yaxis.set_minor_locator(locmin)
    axins1.yaxis.set_minor_formatter(NullFormatter())
    axins1.yaxis.label.set_color(st.get_color())
    axins1.yaxis.label.set_color('C0')  # default matplotlib blue now
    axins1.tick_params(axis='y', colors='C0', which='both')
    axins1.set_xlim(datetime(2006, 9, 26, 0, 0), datetime.now())
    axins1.plot()

    # Version label annotation, including styling of:
    arrow_colour = 'darkgoldenrod'
    for ver, data in totals_figures.items():
        if ver % 5 == 0:  # label points with version number every 5 versions
            x = convert_date_str(data["date"])
            y_diff = data["diff"]
            y_total = data["total"]
            arrow_props = {
                "arrowstyle": "wedge",
                "fc": arrow_colour,
                "ec": arrow_colour,
                "alpha": 0.75,
            }
            ax1.annotate(
                str(ver), xy=(x, y_total), xytext=(x, y_total - 430),
                color=arrow_colour, alpha=0.75, arrowprops=arrow_props
            )
            ax2.annotate(
                "", xy=(x, y_diff), xytext=(dates.date2num(x)+30, y_diff+85),
                color=arrow_colour, arrowprops=arrow_props
            )
            axins1.annotate(
                str(ver), xy=(x, y_diff),
                xytext=(dates.date2num(x)-90, y_diff + 2.25*y_diff),
                color=arrow_colour, arrowprops=arrow_props
            )

    # Show and save:
    plt.savefig(
        os.path.join(VIS_DIR_LOCATION, 'totals-and-diffs-plot.png'),
        format='png'
    )
    plt.show()


def make_plot_against_dates(totals_figures):
    """TODO."""
    make_raw_and_difference_plot(totals_figures)


def make_plot_against_versions(totals_figures):
    """TODO."""
    make_raw_and_difference_plot(totals_figures, by_date=False)


def get_new_names(all_std_names_per_version, newer_version, older_version,
                  print_on=False):
    """TODO."""
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
    """TODO."""
    name_phrase_list = []
    for name in all_names_list:
        phrase = name.replace("_", " ")
        name_phrase_list.append(phrase)
    return name_phrase_list


def print_version_comparison(newer_version, older_version):
    """TODO."""
    new_names = get_new_names(
        get_all_std_names_per_version(
            STD_NAME_ROOT_DIR_RELATIVE_PATH, return_names=True),
        newer_version, older_version
    )
    print("\n\n\n", "-" * 15, "New to v%s" % str(newer_version),
          "-" * 15, "\n\n\n")
    names_spaced = convert_underscored_phrase_to_words(new_names)
    for sname in names_spaced:
        print(sname)
    return " ".join(names_spaced)


def make_wordcloud(text, name):
    """Create word cloud visual for version differences in standard names."""
    wordcloud = WordCloud(
        background_color='white', width=1600, height=800).generate(text)
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(
        os.path.join(VIS_DIR_LOCATION, '{}.png'.format(name)), format='png')
    plt.show()


def main():
    totals_data = get_all_std_names_per_version(
        STD_NAME_ROOT_DIR_RELATIVE_PATH)

    # Send raw/crude table of totals per version to STDOUT:
    pprint.pprint(totals_data)

    # Visualise the above data in various ways & save to 'standard-names-vis':
    # 1. plot of the totals and differences:
    make_plot_against_dates(totals_data)
    # ... noting the spike in totals from versions 11-12 and 48-49. Visualise:
    # 2. ... via word clouds of the names new to the later version:
    make_wordcloud(
        print_version_comparison(12, 11), "wordcloud_diff_12_and_11")
    make_wordcloud(
        print_version_comparison(49, 48), "wordcloud_diff_49_and_48")


if __name__ == "__main__":
    main()
