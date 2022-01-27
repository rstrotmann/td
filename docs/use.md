# Using TD

This gives an overview on how to run the td tool from the command line.

## Requirements

TD is written in python 3. In order to run the tool on your system, python 3 must be installed. You can find out which version of python is installed (or is the default) on your system with `python --version`.

## Installation

TD is provided as a .whl file that can be installed using the python packet manager, pip.

To install the package on your system, run `pip install NAME.whl` from the command line where _NAME_ is the exact name of the provided file (e.g., "td-2.1-py3-none-any.whl"). The filename begins with _td-..._ but the full name is dependent on the release of the specific version, please check your version.


## Running TD

TD is a command line script. Open up a terminal window and enter the TD command in the form `td [OPTIONS] FILE` where _FILE_ corresponds to the json-formatted input file (see [Input](input.md) for details).

As a reference example, the following figure (based on [this](test.json) input file) was rendered running the basic command `td test.json`), i.e., without further OPTIONS:

[![](normal.svg)](test.json)

The following section summarizes the available rendering options (_OPTIONS_) that can be used to further specify the visual output.

The available options can also be shown with `td --help`. In the current version of TD, they include:

| Option| Alternative | Description |
| -- | -- | -- | 
| [--output TEXT](#output-file) | -o | Output file name. Default: INPUT.svg |
| [--fontsize INTEGER](#font-size-and-family) | -s | Output font size (default 11) |
| [--font TEXT](#font-size-and-family) | -f | Output font type (default: Arial) |
| [--padding FLOAT](#padding) | -p | Y-axis padding factor (default 1) |
| [--condensed](#condensed) | -c | Show condensed daygrid |
| [--timescale](#timescale) | -t | Show time scale |
| [--graph](#dose-graph) | -g | Show dose graph |
| [--ellipsis](#ellipsis) | -e | Reduce symbols in condensed output |
| [--footnotes](#footnotes) | -n | Show footnotes |
| --all              | -A | All options, equivalent to -ctge |
| --version          |    | Show version and exit |
| --help             |    | Show this message and exit. |

### Output file

The default output file name is the input file name (e.g., "test.json") with the .svg extension (i.e., "test.svg"). This can be overridden with the _--output_ or _-o_ option.

### Font size and family

The default font is Arial 11 point. Both font and size can be overridden using the _--font_ (_-f_) and _--fontsize_ (_-s_) options. The available font families depend on the fonts installed on the target system.

In addition, the generated svg file can be scaled in the target application (e.g., MS PowerPoint), and any element can be reformatted separately.

### Padding

The parameter _--padding_ (_-p_) increases or decreases the vertical space between period elements. The default of 1 should work in most cases.

### Condensed

This option can be used to compress the visual output horizontally. Period days for which no daylabel has been specified in the input file (see [Period formatting](input.md#period-formatting) in the [Input](input.md) section) will be rendered narrower.

The below version of the above example was rendered using the same [input file](test.json) but with the _--condensed_ option, i.e., running `td --condensed test.json` (or, alternatively, `td -c test.json`):

![](condensed.svg)

### Ellipsis

In addition to condensed output, daily recurring procedure symbols that visually clutter the output can be reduced using the _--ellipsis_ or _-e_ option.  

The below version was rendered running `td -ce test.json` for a combination of condensed and ellipsis output:

![](ellipsis.svg)

### Timescale

Procedures that have exact time information included in the input file, e.g., PK samplings (see ["exact procedure times"](input.md#exact-procedure-times)), can be displayed with an inset figure underneath that shows the timescale detail.

The following output was generated using the `td --condensed --timescale test.json` (or, alternatively, `td -ct test.json`) command:

![](timescale.svg)

Note that that there must be the `"timescale": "show"` line included in the json [input file](test.json) for this to take effect on a procedure (see ["exact procedure times"](input.md#exact-procedure-times)).

For visual clarity, it is recommended to limit display of timescales to the last element (the one at the bottom) of a trial design visualization.

### Dose graph

In cases where intraindividual dose escalation occurs, e.g., to phase in a drug, a dose graph can be shown underneath the administration symbols to indicate the dose over time.

A prerequisite is that the respective dosing information is included per day in the input file (see [Exact dose information](input.md#exact-dose-information) in the [Input](input.md) section).

The following output was generated running the `td --condensed --graph test.json` (or, alternatively, `td -cg test.json`) command to include a dose graph for carbamazepine:

![](graph.svg)

### Footnotes

If footnotes have been defined in the input file (see [Footnotes](input.md#footnotes) in the [Input](input.md) section), they can be rendered in the output using the "--footnotes" (or "-n") option.
