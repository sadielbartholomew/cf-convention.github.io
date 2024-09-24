#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import os
import pprint
import re
from datetime import datetime

import matplotlib.dates as dates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, ScalarFormatter, MultipleLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
import numpy as np
from PIL import Image
from wordcloud import WordCloud, ImageColorGenerator


# Run from root repo dir (or if from 'includes' dir, add initial ".."):
STD_NAME_ROOT_DIR_RELATIVE_PATH = os.path.join("Data", "cf-standard-names")
PWD = os.path.dirname(__file__)

XML_STD_NAME_TAG_PATTERN = re.compile(r"<entry id=\"(.+)\">")
XML_LAST_MODIFIED_PATTERN = re.compile(r"<last_modified>(.+)T(.+)</last_modified>")

COLOUR_1 = "dodgerblue"
COLOUR_2 = "crimson"
COLOUR_3 = "darkgoldenrod"

TOTALS_PLOTNAME = "sn_totals_plot"
WORDCLOUD_PLOTNAME_PREFIX = "sn_wordcloud"


def get_from_file(pattern, std_name_xml_filename):
    """TODO."""
    extracted_data = []
    with open(std_name_xml_filename, "rt") as std_name_xml_data:
        for line in std_name_xml_data:
            full_pattern_result = pattern.search(line)
            if full_pattern_result:
                extracted_data.append(full_pattern_result.group(1).rstrip("\n"))
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
                if filename.endswith("cf-standard-name-table.xml"):
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
            except:
                print(
                    f"WARNING: for version {version} from {filename} could "
                    "not get date, so assumed and registered with a known "
                    "date for version 1."
                )
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
    # Copy to ensure original dictionary isn't changed in-place here
    totals_with_diff_data = deepcopy(totals_data)

    totals_with_diff_data[1].update({"diff": 0})
    for ver, data in totals_data.items():
        if ver == 1:
            continue
        else:
            try:
                previous_ver_data = totals_with_diff_data[ver - 1]
            except KeyError:  # account for case of v39 (v38 was skipped)
                previous_ver_data = totals_with_diff_data[ver - 2]
            totals_with_diff_data[ver].update(
                {"diff": data["total"] - previous_ver_data["total"]}
            )
    return totals_with_diff_data


def process_current(totals):
    """TODO."""
    # Copy to ensure original dictionary isn't changed in-place here
    totals_figures = deepcopy(totals)

    # Convert versions to integers for plotting:
    current_data = totals_figures["current"]
    totals_figures = {
        int(ver): data for ver, data in totals_figures.items() if ver != "current"
    }
    # Convert current to assumed latest version, for plotting version as int:
    highest_vesion = max(totals_figures.keys())
    assume_current_version = highest_vesion + 1

    # New dict
    processed_totals = totals_figures.copy()
    processed_totals[assume_current_version] = current_data
    return processed_totals


def pre_process(all_totals):
    """Any processing on the raw data required pre-plot."""
    # Copy to ensure original dictionary isn't changed in-place here
    all_totals_data = deepcopy(all_totals)
    
    # Convert 'current' to latest version number (assumed)
    pre_procd_totals = process_current(all_totals_data)

    # Convert version strings to integers so they become plotable
    pre_procd_totals = {int(ver): data for ver, data in pre_procd_totals.items()}

    # Version 23 date issue, remove extra character that shouldn't be there:
    date_v23 = pre_procd_totals[23]["date"]
    pre_procd_totals[23]["date"] = date_v23.strip(":")

    # Get diffs:
    pre_procd_totals = calculate_difference_totals(pre_procd_totals)

    return pre_procd_totals


def convert_date_str(date_str):
    """TODO."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def make_raw_and_difference_plot(totals_figures, by_date=True):
    """TODO."""
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

    sorted_totals = sorted(totals.items())
    sorted_diffs = sorted(diffs.items())

    plt.rcParams.update({"font.size": 12})
    fig, ax1 = plt.subplots(figsize=(12, 10))
    ax1.set_title(
        (
            "Number of CF Conventions Standard Names in the table "
            "by date and per version"
        ),
        fontsize=18,
    )
    # Remove horizontal space between axes
    fig.subplots_adjust(hspace=0)
    ax1.set_xlabel("Date, marked each year at January 1st", fontsize=17)
    ax1.tick_params(axis="x", which="minor")
    ax1.set_ylabel("Total number of names", fontsize=17)
    ax1.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax2 = ax1.twinx()
    ax2.set_ylabel(
        "Difference in total number of names relative to previous version (log scale)",
        fontsize=16,
        rotation=270,
        labelpad=20,
    )
    # Use 'symlog' not 'log' so we can include zero values
    ax2.set_yscale("symlog")
    ax2.yaxis.set_major_formatter(ScalarFormatter())

    ax1.step(
        *zip(*sorted_totals),
        where="post",
        linestyle="-",
        color=COLOUR_2,
        linewidth=LINEWIDTH,
        zorder=1000,  # ensure in foreground to everything except scatter plot
        label="Total number (see left y-axis)",
    )
    ax1.yaxis.label.set_color(COLOUR_2)

    ax1.yaxis.set_major_locator(MultipleLocator(500))

    ax2.set_zorder(3)
    dt = ax2.scatter(
        *zip(*sorted_diffs),
        s=20,
        color=COLOUR_1,
        label="Difference in total number (see right y-axis)",
    )

    # Version label annotation:
    for ver, data in totals_figures.items():
        # Annotate version every 5 versions, also first as core one
        if ver % 5 == 0 or ver == 1:
            # Annotations above with arrows pointing down mostly, to avoid
            # overlaying the plot lines, but for the last versions have the
            # annotation below with arrows pointing up, to avoid them
            # scrolling off the side of the plot.
            x = convert_date_str(data["date"])
            y_diff = data["diff"]
            y_total = data["total"]

            y_offset = y_total + 200
            if ver >= 60:
                # Bit more than -200, inverse to above, to cover arrow size
                y_offset = y_total - 300

            final_annotation = ax1.annotate(
                str(ver),
                xy=(x, y_total),
                xytext=(x, y_offset),
                color=COLOUR_3,
                alpha=0.6,
                arrowprops=dict(
                    arrowstyle="simple",
                    fc=COLOUR_3,
                    ec=COLOUR_3,
                    shrinkA=0.2,
                    shrinkB=0.2,
                ),
                ha="center",
            )
            # For scatter, circle in the same colour to avoid more arrows
            # which will clutter, tied by having the same colour
            final_scatter_item = ax2.scatter(
                x,
                y_diff,
                facecolors="none",
                edgecolors=COLOUR_3,
                alpha=0.75,
                linewidth=1.5,
                s=80,
                zorder=1001,  # ensure at the very front, even to step plot
            )

    # Set the labelling for the legend only one scatter item for the
    # every 5 version markers, to avoid duplicate legend items
    final_scatter_item.set_label(
        "Marks every five versions (plus the first) on difference",
    )
    ax2.yaxis.label.set_color(COLOUR_1)

    ax1.set_ylim(bottom=0)
    # symlog specification makes log-scale ticks difficult, so simplest to
    # explicitly set the minor ticks, like so
    ax2.set_yticks([0, 1, 10, 100, 1000])
    ax2.set_yticks(
        [
            0,
        ]
        + list(range(1, 10))
        + list(range(10, 100, 10))
        + list(range(100, 1100, 100)),
        minor=True,
    )
    ax1.tick_params(axis="y", which="both", colors=COLOUR_2)
    ax2.tick_params(axis="y", which="both", colors=COLOUR_1)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    # Add layout
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines
        + lines2
        + [
            final_annotation.arrow_patch,
        ],
        labels
        + labels2
        + [
            "Labels every five versions (plus the first) on total",
        ],
        loc="upper left",
        fontsize=14,
    )

    plt.savefig(os.path.join(PWD, TOTALS_PLOTNAME))
    plt.show()


def make_plot_against_dates(totals_figures):
    """TODO."""
    make_raw_and_difference_plot(totals_figures)


def make_plot_against_versions(totals_figures):
    """TODO."""
    make_raw_and_difference_plot(totals_figures, by_date=False)


def get_new_names(
    all_std_names_per_version, newer_version, older_version, print_on=False
):
    """TODO."""
    newer_set = set(all_std_names_per_version[str(newer_version)])
    older_set = set(all_std_names_per_version[str(older_version)])
    difference = list(newer_set.difference(older_set))

    if print_on:
        print("New names:")
        pprint.pprint(newer_set)
        print("\n\nOld names:")
        pprint.pprint(newer_set)
        print("\n\nAdded names from new to old versions:")
        pprint.pprint(difference)

    return difference


def convert_underscored_phrase_to_words(all_names_list):
    """TODO."""
    name_phrase_list = []
    for name in all_names_list:
        phrase = name.replace("_", " ")
        name_phrase_list.append(phrase)
    return name_phrase_list


def print_version_comparison(
        newer_version, older_version, print_totals_only=True):
    """TODO."""
    new_names = get_new_names(
        get_all_std_names_per_version(
            STD_NAME_ROOT_DIR_RELATIVE_PATH, return_names=True
        ),
        newer_version,
        older_version,
    )
    names_spaced = convert_underscored_phrase_to_words(new_names)

    if print_totals_only:
        print(
            f"For {newer_version} to {older_version}, {len(new_names)} "
            f"new names added."
        )
    else:
        print(
            f"For {newer_version} to {older_version}, names added are:\n"
            f"{'\n'.join(names_spaced)}"
        )

    return " ".join(names_spaced)


def make_wordcloud(
        newer_version, older_version=False, print_totals_only=True):
    """Create wordcloud for version differences in standard names."""
    # If no older version specified, make it the one before set newer version
    if not older_version:
        older_version = newer_version - 1

    text = print_version_comparison(
        newer_version, older_version,
        print_totals_only=print_totals_only,
    )

    # Define a Robinson projection shape to use as the wordcloud outline shape
    image_shape = np.array(
        Image.open(
            os.path.join(PWD, "robinson_proj_shape_cartopy.png"))
    )

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        # Use an earth-like colour scheme for geoscience scope
        colormap="gist_earth",
        mask=image_shape,
    ).generate(text)

    plt.imshow(
        wordcloud,
        interpolation="bilinear",
    )
    plt.axis("off")
    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PWD,
            f"{WORDCLOUD_PLOTNAME_PREFIX}_versions"
            f"{older_version}_to_{newer_version}"
        ),
        dpi=1000,
    )
    plt.show()


def main():
    """TODO."""
    totals_data = get_all_std_names_per_version(STD_NAME_ROOT_DIR_RELATIVE_PATH)
    diff_data = calculate_difference_totals(pre_process(totals_data))

    # State figures
    print("Totals:")
    pprint.pprint(totals_data)
    print("Totals and differences:")
    pprint.pprint(diff_data)

    # Plot of totals and differences together
    make_plot_against_dates(totals_data)

    # Word clouds of new news added in a given version range, or for full table
    make_wordcloud(12)
    make_wordcloud(49)
    make_wordcloud(86, print_totals_only=False)


if __name__ == "__main__":
    main()
