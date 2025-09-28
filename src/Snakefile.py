rule tag_nvim:
    input:
        '../data/interim/{nvim}_results.tsv',
    output:
        '../data/interim/tmp/{nvim}_results.tsv',
    shell:
        'python tag_nvim.py {wildcards.nvim} {input} {output}'

rule cat_dist:
    input:
        expand('../data/interim/tmp/{nvim}_results.tsv', nvim=('nord', 'dracula', 'catppuccin'))
    output:
        '../data/end/dist.tsv',
    shell:
        'python-cath {input} {output}'

rule all:
    input:
        '../data/end/dist.tsv',
