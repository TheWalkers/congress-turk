import argparse
import yaml
from itertools import groupby

parser = argparse.ArgumentParser(description=
    'Patch office details into main file')
parser.add_argument("patch",
    help="File with offices to patch in",
    type=argparse.FileType('r'),
    default='-')
parser.add_argument("source",
    help="source (legislators-district-offices.yaml)",
    type=argparse.FileType('r', 0))
parser.add_argument("destination",
    help="destination for patched results (legislators-district-offices.yaml)",
    type=argparse.FileType('w', 0),
    default='-')
args = parser.parse_args()

patch = yaml.load(args.patch)
main = yaml.load(args.source)
by_id = {r['id']['bioguide']: r for r in main}
for r in patch:
    by_id[r['id']['bioguide']]['offices'] = r['offices']

args.destination.truncate()
args.destination.write(yaml.dump(main, default_flow_style=False))

