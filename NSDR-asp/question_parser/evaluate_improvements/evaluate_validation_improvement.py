"""Evaluate validation set improvement"""
import json

UNMATCHED = 1

#OE
# file_path = 'oe_1000pg_val_new.json'
file_path = '../oe_val_core.json'
with open(file_path) as f:
    baseline = json.load(f)

total_question_count = 0
wrong_question_count = 0

for i in range(5000):
    b = baseline[f'{10000 + i}']
    for q, bq in enumerate(b['questions']):  # Sometimes the order is not same, so use 2 for loops
        total_question_count += 1
        if bq['program'] != bq['program_gt']:
            wrong_question_count += 1
print("Evaluate oe")
print(f'-- wrong question: {wrong_question_count} / {total_question_count} --')


# MC
# file_path = 'mc_1000q_4000c_val_new.json'
file_path = '../mc_val_core.json'
gt_path = 'validation.json'
with open(file_path) as f:
    baseline = json.load(f)
with open(gt_path) as f:
    ground_truth = json.load(f)

total_question_count = 0
wrong_question_count = 0
total_choice_count = 0
wrong_choice_count = 0

for i in range(5000):
    b = baseline[f'{10000 + i}']
    g = ground_truth[i]
    total_question_count += len(b['questions'])

    for q, bq in enumerate(b['questions']):  # Sometimes the order is not same, so use 2 for loops
        for gq in g['questions'][10:]:  # mc questions

            # Match question
            if bq['question'] == gq['question']:
                gq['program'] = ['filter_counterfact' if x == 'get_counterfact' else x for x in gq[
                    'program']]  # `get_counterfact` is used in gq, whereas, `filter_counterfact` is used in bq.
                if bq['question_program'] != gq['program']:  # if bq['program_gt'] != gq['program']:
                    wrong_question_count += 1
                    print(f'scene{i}-Q{q} baseline:', bq['question_program'], ', gt:', gq['program'])
                    print()
                    bq['question_program'] = gq['program']

                # Match choices
                total_choice_count += len(bq['choices'])
                unmatched = [UNMATCHED] * len(bq['choices'])
                for j, bc in enumerate(bq['choices']):
                    for gc in gq['choices']:
                        if bc['program'] == gc['program']:
                            unmatched[j] = 0
                            break

                wrong_choice_count += sum(unmatched)
                if sum(unmatched) > 0:
                    for j, u in enumerate(unmatched):
                        if u == UNMATCHED:
                            print(f'scene{i}-Q{q}-C{j} baseline:', bq['choices'][j]['program'], ', gt:')
                            for gc in gq['choices']:
                                print(gc['program'])
                            print()
                            # bq['choices'][j]['program'] = gq['choices'][m[j]]['program']
                            # bq['choices'][j]['answer'] = gq['choices'][m[j]]['answer']

print("Evaluate mc")
print(f'-- wrong question: {wrong_question_count} / {total_question_count} --')
print(f'-- wrong choice: {wrong_choice_count} / {total_choice_count} --')
