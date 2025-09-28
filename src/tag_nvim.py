import sys

nvim, in_tsv, out_tsv = sys.argv[1:]
with open(out_tsv, "w") as fout, open(in_tsv) as fin:
    header = fin.readline().strip()
    fout.write(f"{header}\tnvimTheme\n")
    for line in fin:
        line = line.strip()
        if not line:
            continue
        fout.write(f"{line}\t{nvim}\n")
