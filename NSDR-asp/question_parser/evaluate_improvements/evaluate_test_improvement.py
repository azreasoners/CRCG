"""Evaluate test set improvement"""
import json

UNMATCHED = 1

# OE
author_path = 'oe_parsed_prog_1000_test.json'
ours_path = '../oe_test_core.json'

with open(author_path) as f:
    baseline = json.load(f)
with open(ours_path) as f:
    ours = json.load(f)

total_question_count = 0
wrong_question_count = 0
for i, (b, o) in enumerate(zip(baseline, ours)):
    for j, (bq, oq) in enumerate(zip(b['questions'], o['questions'])):
        total_question_count += 1
        if bq['program'] != oq['program']:
            wrong_question_count += 1
            # print(f'{i} - {j}', bq['question_id'])
print("Evaluate oe")
print(f'-- wrong question: {wrong_question_count} / {total_question_count} --')


# MC
author_path = 'mc_parsed_prog_1000_test.json'
ours_path = '../mc_test_core.json'
with open(author_path) as f:
    baseline = json.load(f)
with open(ours_path) as f:
    ours = json.load(f)

total_question_count = 0
wrong_question_count = 0
total_choice_count = 0
wrong_choice_count = 0
for i, (b, o) in enumerate(zip(baseline, ours)):
    for j, (bq, oq) in enumerate(zip(b['questions'], o['questions'])):
        total_question_count += 1
        if bq['program'] != oq['program']:
            wrong_question_count += 1
            # print(f'{i} - {j}', qb['question_id'])

        total_choice_count += len(bq['choices'])
        unmatched = [UNMATCHED] * len(bq['choices'])
        for k, bc in enumerate(bq['choices']):
            for oc in oq['choices']:
                if bc['program'] == oc['program']:
                    unmatched[k] = 0
                    break

        wrong_choice_count += sum(unmatched)
        if sum(unmatched) > 0:
            for k, u in enumerate(unmatched):
                if u == UNMATCHED:
                    print(f'scene{i}-Q{j}-C{k} baseline:', bq['choices'][k]['program'], ', gt:')
                    for oc in oq['choices']:
                        print(oc['program'])
                    print()

print("Evaluate oe")
print(f'-- wrong question: {wrong_question_count} / {total_question_count} --')
print(f'-- wrong choice: {wrong_choice_count} / {total_choice_count} --')
