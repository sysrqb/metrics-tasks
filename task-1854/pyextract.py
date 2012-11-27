import os
import sys

def main():
    out_file = open('linf-extracted.csv', 'w')
    prev_validafter, max_validafter = '', ''
    max_lines = []
    prev_relays, prev_min_adv_bw = 0, 0
    for line in open('linf.csv'):
        parts = line.strip().split(',')
        validafter = parts[0]
        min_adv_bw = int(parts[1])
        relays = int(parts[2])
        linf = parts[3]
        if validafter != prev_validafter:
            prev_relays, prev_min_adv_bw, excluded_adv_bw = 0, 0, 0
            next_cutoffs = [0, 10000, 20000, 30000, 40000, 50000, 75000,
                    100000, 100000000000000000000]
        excluded_adv_bw += (prev_relays - relays) * prev_min_adv_bw
        extended_line = "%s,%d" % (line.strip(), excluded_adv_bw, )
        if validafter > max_validafter:
            max_validafter = validafter
            max_lines = []
        if validafter == max_validafter:
            max_lines.append(extended_line)
        while min_adv_bw >= next_cutoffs[0]:
            out_file.write("%s,%d,%d,%s,%d,history\n" % (validafter,
                    next_cutoffs[0], relays, linf, excluded_adv_bw, ))
            next_cutoffs.pop(0)
        prev_validafter = validafter
        prev_relays = relays
        prev_min_adv_bw = min_adv_bw
    for line in max_lines:
        out_file.write(line + ",last\n")
    out_file.close()
    prob_out_file = open('prob-extracted.csv', 'w')
    for line in open('prob.csv'):
        if line.startswith(max_validafter):
            prob_out_file.write(line.strip() + '\n')
    prob_out_file.close()

if __name__ == '__main__':
    main()

