
import os
import json
import pathlib
from td.td import *


def test_render_td():
    test_files = [i for i in pathlib.Path(r'./td/tests/fixtures').glob('*.json')]
    for tf in test_files:
        print(tf.stem)
        with open(tf) as f:
            td_dict = json.load(f)
        assert(render_td(td_dict))
