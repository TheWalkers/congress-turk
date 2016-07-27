import re
import string

from reconcile_turk_results import TurkResultReconciler

def normalize_phone(phone):
    return re.sub(r'.*(\d{3}).*(\d{3}).*(\d{4}).*', r'\1-\2-\3', phone)


class DetailTaskResultReconciler(TurkResultReconciler):
    def preprocess_row(self, row):
        for field, answer in self.answers(row).items():
            if answer == '{}':
                row[field] = ''

        for field in ['Answer.phone', 'Answer.fax']:
            row[field] = normalize_phone(row[field])
        return row


if __name__ == '__main__':
    DetailTaskResultReconciler().reconcile_results()

