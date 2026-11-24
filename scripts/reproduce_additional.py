"""Reproduce the three additional experiments without running the extended-numerics suite.

The full release reproducibility command is scripts/reproduce_all.py; this
focused command is useful for quickly checking the new independent methods.
Only the comparative-cost, workplace-contact, and truncation-accuracy outputs are touched. Input data and prior
approved numerical experiments are never modified by this entry point.
"""
from __future__ import annotations
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCR=ROOT/'experiments/scripts'
DATA=ROOT/'experiments/data'

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    for stage,out,extra in (
        ('carleman_cost_comparison.py','carleman_costs.csv',['--repeats','5']),
        ('sociopatterns_workplace.py','workplace_topology.csv',['--repeats','30']),
        ('truncation_accuracy.py','truncation_accuracy.csv',[]),
    ):
        # The SocioPatterns stage writes four related files to a directory;
        # the other additional stages produce one named CSV each.
        target = DATA if stage == 'sociopatterns_workplace.py' else DATA / out
        command=[sys.executable,str(SCR/stage),'--repo',str(ROOT),'--out',str(target),*extra]
        print('RUN',stage,flush=True)
        subprocess.run(command,cwd=ROOT,check=True)
    print('ADDITIONAL_EXPERIMENTS_PASS',flush=True)
if __name__=='__main__':
    main()
