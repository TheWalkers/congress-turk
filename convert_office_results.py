import argparse
import csv
import yaml
from itertools import groupby

parser = argparse.ArgumentParser(description=
    'Convert results of a "details" task to yaml')
parser.add_argument("source",
    help="Reconciled CSV results of MTurk HITs.",
    type=argparse.FileType('r'),
    default='-')
parser.add_argument("destination",
    help="destination for results (legislators-district-offices.yaml)",
    type=argparse.FileType('w', 0),
    default='-')
args = parser.parse_args()

by_id = lambda row: row.get('Input.id')

rows = list(csv.DictReader(args.source))

rows.sort(key=by_id)
grouped = groupby(rows, key=by_id)

data = []
for key, group in grouped:
    offices = []
    for item in group:
        office = {k.replace("Answer.", ""): v
                  for k, v in item.items()
                  if k.startswith("Answer.")}
        offices.append(office)

    offices.sort(key=lambda o: o.get('city'))

    data.append({'id': {'bioguide': key}, 'offices': offices})

out = yaml.safe_dump(data, default_flow_style=False, encoding='utf-8')
args.destination.write(out)
