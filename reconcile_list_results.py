import re
import string

from reconcile_turk_results import TurkResultReconciler

class ListTaskResultReconciler(TurkResultReconciler):
    def preprocess_row(self, row):
        offices = [o.strip()
                   for o in row['Answer.district_offices'].strip().split('\n')]
        office_suffix = re.compile(r'( district)? office$', re.I)
        offices = [office_suffix.sub('', o) for o in offices]
        dc = re.compile('washington,? d\.?c\.?', re.I)
        offices = [o for o in offices if not dc.match(o)]
        offices.sort(key=string.lower)
        row['Answer.district_offices'] = offices
        return row

    def postprocess_row(self, row):
        row['Answer.district_offices'] = '\n'.join(row['Answer.district_offices'])
        return row


if __name__ == '__main__':
    ListTaskResultReconciler().reconcile_results()

