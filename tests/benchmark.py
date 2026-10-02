"""Opt-in sequential guidance comparison; no API fallback or production data.

python tests/benchmark.py --host gpu1 --output /fresh/path --seconds 60
This compares guidance only. Legacy hooks stay inactive behind common OS isolation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentctl import transport
from agentctl.common import execute, write_json

CASES = {
    "bugfix": ({"stats.py": "def median(values):\n    values = sorted(values)\n    return values[len(values)//2]\n"},
        "Fix stats.median: empty inputs return None, even lengths return the mean of the two central values, odd lengths return the central value. Preserve the input sequence.",
        "from stats import median; assert median([]) is None; assert median([7])==7; assert median([4,1,2,3])==2.5; assert median([-3,-1])==-2; a=[3,1,2]; assert median(a)==2 and a==[3,1,2]"),
    "multi-file": ({"parse.py": "def parse_size(text):\n    return int(text)\n", "app.py": "from parse import parse_size\ndef total_bytes(values):\n    return sum(parse_size(value) for value in values)\n"},
        "Extend parse.parse_size and app.total_bytes to accept nonnegative integer byte counts, decimal KB/MB and binary KiB/MiB suffixes, case-insensitively with optional whitespace between the number and suffix, plus surrounding whitespace. Reject malformed values, fractional bytes and negative counts with ValueError. Keep the public functions.",
        "from parse import parse_size; from app import total_bytes; assert parse_size(' 2 kiB ')==2048; assert parse_size('3MB')==3000000; assert parse_size('2 MiB')==2097152; assert total_bytes(['1KB','2KiB','3'])==3051;\nfor value in ['-1','1.5','NaN','2GB','nonsense']:\n try: parse_size(value)\n except ValueError: pass\n else: raise AssertionError(value)"),
    "research": ({"analysis.py": "import csv\ndef summarize(path):\n    with open(path) as stream:\n        values = [float(row['value']) for row in csv.DictReader(stream)]\n    return {'n': len(values), 'mean': sum(values)/len(values)}\n", "data.csv": "value\n1\n2\n3\nNaN\nbad\ninf\n"},
        "Fix analysis.summarize to exclude nonfinite and malformed observations, report n, excluded, mean and median, and return None for mean and median when no valid observations exist. Preserve raw data.csv. Add a meaningful check using the real CSV input.",
        "import hashlib; from pathlib import Path; from analysis import summarize; assert summarize('data.csv')=={'n':3,'excluded':3,'mean':2.0,'median':2.0}; assert hashlib.sha256(Path('data.csv').read_bytes()).hexdigest()=='DATA_HASH'"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    package = Path(__file__).resolve().parents[1]
    archive = package / 'archive/server-config-2026-09/.agent-rules'
    guidance = {'native': '', 'legacy': (archive/'AGENTS.md').read_text()+'\n'+(archive/'harness/codex/codex.md').read_text(),
                'slim': (package/'agentctl/content/personal.md').read_text()}
    report = {'scope': 'guidance ablation with fixed native model, safety isolation and checks; legacy hooks not activated',
              'host': args.host, 'created': time.time(), 'per_task_seconds': args.seconds, 'runs': []}
    for case, (files, prompt, grade) in CASES.items():
        repository = root / case
        repository.mkdir()
        for name, content in files.items():
            (repository/name).write_text(content)
        execute(['git','init','-b','main'], cwd=repository)
        execute(['git','-c','user.name=Benchmark','-c','user.email=benchmark@example.invalid','add','.'], cwd=repository)
        execute(['git','-c','user.name=Benchmark','-c','user.email=benchmark@example.invalid','commit','-m','immutable benchmark fixture'], cwd=repository)
        if 'data.csv' in files:
            grade = grade.replace('DATA_HASH', hashlib.sha256(files['data.csv'].encode()).hexdigest())
        for label, text in guidance.items():
            spec = {'kind':'agent','harness':'codex','repo':str(repository),'revision':'HEAD','changes':[],
                    'seconds':args.seconds,'resources':{'cpu_threads':2,'memory_mb':8192},'publish':False,
                    'prompt':prompt, 'checks':[['python3','-c',grade]], 'read_only':['data.csv'] if 'data.csv' in files else [],
                    'evaluation_guidance':{'label':label,'text':text}}
            initial = transport.dispatch(args.host, spec)
            task = initial['id']
            entry = {'case':case,'guidance':label,'task':task,'instruction_words':len(text.split()),'status':'prepared'}
            report['runs'].append(entry)
            write_json(root/'report.json',report)
            print(json.dumps(entry),flush=True)
            # Never replay a lost task. A lost status reply ends the experiment.
            while True:
                result = json.loads(transport.remote(args.host,['status',task]))
                if result['status'] not in {'prepared','running'}:
                    break
                time.sleep(2)
            entry.update(status=result['status'], seconds=result['spent_seconds'], checks=result['checks'],
                         native_session=result.get('native_session'), reason=result.get('reason'), human_review='pending')
            destination = root / f'{case}-{label}-evidence'
            transport.extract(transport.remote(args.host,['_export',task],timeout=120),destination)
            usages = []
            for line in (destination/'worker.jsonl').read_text().splitlines():
                try:
                    event = json.loads(line)
                    if event.get('usage'): usages.append(event['usage'])
                except ValueError: pass
            entry['native_usage'] = usages
            write_json(root/'report.json',report)
            print(json.dumps(entry),flush=True)
            if result['status']=='unknown' or 'quota' in str(result.get('reason','')).lower():
                raise SystemExit('Stopped; inspect existing task, no replay or provider fallback')
    print(str(root/'report.json'),flush=True)

if __name__=='__main__': main()
