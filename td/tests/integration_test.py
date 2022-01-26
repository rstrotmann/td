import sys
import json
import pathlib
from td.td import *


# def test_render_td():
#     test_files = [i for i in pathlib.Path(r'./td/tests/fixtures').glob('*.json')]
#     for tf in test_files:
#         print(tf.stem)
#         with open(tf) as f:
#             td_dict = json.load(f)
#         assert(render_td(td_dict))


def _make_svg(infile, outfile, *, condensed=False, autocompress=False, ellipsis=False, footnotes=False, graph=False, timescale=False):
    with open(infile) as f:
        td_dict = json.load(f)
    svg_out = render_td(td_dict, title=infile.stem, debug=debug, condensed=condensed, autocompress=autocompress, timescale=timescale, ellipsis=ellipsis, footnotes=footnotes, graph=graph, fontsize=14)
    with open(outfile, "w") as f:
        f.write(svg_out)
    return


def test_svg_output():
    inpath = pathlib.Path(r'./td/tests/fixtures')
    outpath = pathlib.Path(r'./td/tests/output')
    test_files = [i for i in inpath.glob('*.json')]
    for infile in test_files:
        print(infile)
        outfile = outpath.joinpath(infile.stem + ".svg")
        _make_svg(infile, outfile, condensed=True, ellipsis=True, footnotes=True, graph=True, timescale=True)
