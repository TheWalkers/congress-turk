import re
import string

from reconcile_turk_results import TurkResultReconciler

def remove_empty(s):
    if s == '{}':
        s = ''
    return s

def remove_not_available(s):
    return re.sub(r'^n\s*\/\s*a$', '', s.strip(), flags=re.I)

def normalize_phone(phone):
    return re.sub(r'.*(\d{3}).*(\d{3}).*(\d{4}).*', r'\1-\2-\3', phone)


class DetailTaskResultReconciler(TurkResultReconciler):

    answer_processors = [
        remove_empty,
        remove_not_available,
    ]

    def preprocess_row(self, row):
        for field, answer in self.answers(row).items():
            for proc in self.answer_processors:
                answer = proc(answer)
            row[field] = answer

        for field in ['Answer.phone', 'Answer.fax']:
            row[field] = normalize_phone(row[field])
        return row


if __name__ == '__main__':
    DetailTaskResultReconciler().reconcile_results()

