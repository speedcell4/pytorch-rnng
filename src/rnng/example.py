from typing import List, Tuple

from torchtext.data import Example, Field

from rnng.actions import NTAction
from rnng.oracle import Oracle


def make_example(oracle: Oracle, fields: List[Tuple[str, Field]]):
    actions = [str(a) for a in oracle.actions]
    nonterms = [a.label for a in oracle.actions if isinstance(a, NTAction)]
    return Example.fromlist(
        [actions, nonterms, oracle.pos_tags, oracle.words], fields
    )