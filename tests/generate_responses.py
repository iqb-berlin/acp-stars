#!/usr/bin/env python3
"""Build dummy testcenter response reports for a group booklet.

Writes one CSV report plus its JSON conversion per testtaker group:

    tests/responses_<booklet>_<code>.csv
    tests/responses_<booklet>_<code>.json

for the groups configured in CONFIGS, using their logins in the testtaker
file and the units of the booklet. Existing files for these groups are
overwritten; the values are random, so every run gives different data.

Right answers come from each unit's .voud (`variableInfo` of the `interact`
variable), not from this script:
  * codingSource VALUE            - the value of the code with score > 0.
  * codingSource SUM_CHAR_MATCHES - `codingSourceParameter` (e.g. "011000");
                                    code = score = number of matching
                                    characters. Only the full match counts
                                    as right.

Conventions (mimicking responses_sp1g_{8uxhm,a8x9e,ldk82}):
  * rows        - one per login and unit, sorted by unit name.
  * interact    - status CODING_COMPLETE. Wrong values are random other
                  values: another option number for single-select buttons
                  and drop units, another 0/1 string for multi-select. Each
                  login gets a random share of right answers between 35% and
                  90% of the scored units.
  * telemetry   - mainAudio on every scored unit, AudioFeedback on units
                  whose .voud defines audioFeedback, VIDEO on video units,
                  all VALUE_CHANGED. RH units have no responses.
  * ts          - increasing in booklet order, 0.85-5.3 s per unit; logins
                  10,000 s apart, groups 300,000 s apart.
  * JSON        - top-level array, `responses` parsed, inner `content` and
                  `laststate` kept as strings; checked against the existing
                  responses_sp1g_8uxhm.json before anything is written.

Usage: python3 tests/generate_responses.py sp1g|ma1g
"""
import csv
import io
import json
import math
import random
import sys
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

CONFIGS = {
    'sp1g': {
        'units': 'Sp1',
        'groups': ['gazul', '7ttgf', 'vdvl1', 'gp0wz', 'yqhsj'],
        'start_ts': 1785200000000,
        'int_drop': True,  # dnd_Koffer reports 1 / 0 as numbers
    },
    'ma1g': {
        'units': 'Ma1',
        'groups': ['a5u4x', 'a8x9e', '8uxhm', 'ldk82', 'gazul', '7ttgf', 'vdvl1', 'gp0wz', 'yqhsj'],
        'start_ts': 1787000000000,
        'int_drop': False,  # dnd_Muscheln reports the option number as string
    },
}

rng = random.SystemRandom()

LS_RH1 = '{"PLAYER":"RUNNING","CURRENT_PAGE_NR":"undefined","CURRENT_PAGE_ID":"-1","PAGE_COUNT":"0"}'
LS_RH = '{"PLAYER":"RUNNING"}'
LS_VID = '{"PLAYER":"RUNNING","PRESENTATION_PROGRESS":"complete","RESPONSE_PROGRESS":"none"}'
LS_ITEM = '{"PLAYER":"RUNNING","PRESENTATION_PROGRESS":"%s","RESPONSE_PROGRESS":"complete"}'
HEADER = ['groupname', 'loginname', 'code', 'bookletname', 'unitname', 'originalUnitId', 'responses', 'laststate']


def compact(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)


class Unit:
    """What a unit reports, read from its .voud."""

    def __init__(self, folder, unit_id, int_drop):
        definition = json.loads((REPO / 'units' / folder / f'{unit_id}.voud').read_text(encoding='utf-8'))
        self.id = unit_id
        self.kind = definition.get('interactionType')
        self.feedback = 'audioFeedback' in definition
        self.int_drop = int_drop and self.kind == 'DROP'
        info = [v for v in definition.get('variableInfo', []) if v['variableId'] == 'interact']
        self.scored = bool(info)
        if not self.scored:
            if self.kind not in (None, 'VIDEO'):
                raise SystemExit(f'{unit_id}: {self.kind} without interact coding')
            return
        params = definition['interactionParameters']
        options = params['options']
        self.n_options = len(options['buttons'] if isinstance(options, dict) else options)
        self.multi = bool(params.get('multiSelect'))
        self.source = info[0]['codingSource']
        if self.source == 'SUM_CHAR_MATCHES':
            self.right = info[0]['codingSourceParameter']
        elif self.source == 'VALUE':
            right = [c for c in info[0]['codes'] if c['score'] > 0 and c['method'] == 'EQUALS']
            if len(right) != 1 or len(info[0]['codes']) != 1:
                raise SystemExit(f'{unit_id}: no single right answer in {info[0]["codes"]}')
            self.right = right[0]['parameter']
        else:
            raise SystemExit(f'{unit_id}: unknown codingSource {self.source}')

    def answer(self, ok):
        """(value, code, score) of a right or a wrong answer"""
        if self.source == 'SUM_CHAR_MATCHES':
            value = self.right
            while not ok and value == self.right:
                value = ''.join(rng.choice('01') for _ in self.right)
            matches = sum(a == b for a, b in zip(value, self.right))
            return value, matches, matches
        if self.int_drop:
            return (1, 1, 1) if ok else (0, 0, 0)
        if ok:
            return self.right, 1, 1
        if self.multi:
            while True:
                value = ''.join(rng.choice('01') for _ in range(self.n_options))
                if value != self.right:
                    return value, 0, 0
        return rng.choice([str(i) for i in range(1, self.n_options + 1) if str(i) != self.right]), 0, 0


def var(id_, value, status='VALUE_CHANGED', code=0, score=0):
    return {'id': id_, 'status': status, 'value': value, 'code': code, 'score': score}


def main_audio():
    return 1 if rng.random() < 1 / 3 else rng.random()


def to_csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_ALL, lineterminator='\n')
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buf.getvalue()


def csv_to_json(text):
    out = []
    for r in csv.DictReader(io.StringIO(text), delimiter=';'):
        out.append({
            'groupname': r['groupname'], 'loginname': r['loginname'], 'code': r['code'],
            'bookletname': r['bookletname'], 'unitname': r['unitname'],
            'responses': json.loads(r['responses']), 'laststate': r['laststate'],
            'originalUnitId': r['originalUnitId'],
        })
    return json.dumps(out, indent=2, ensure_ascii=False) + '\n'


def check_format():
    """The writers must reproduce an existing report byte-for-byte."""
    ref = (HERE / 'responses_sp1g_8uxhm.csv').read_text(encoding='utf-8')
    assert to_csv(list(csv.reader(io.StringIO(ref), delimiter=';'))[1:]) == ref
    assert csv_to_json(ref) == (HERE / 'responses_sp1g_8uxhm.json').read_text(encoding='utf-8')


def login_rows(group_id, login, booklet_name, units, ts):
    scored = [u.id for u in units if u.scored]
    k = rng.randint(math.ceil(0.35 * len(scored)), math.floor(0.90 * len(scored)))
    correct = set(rng.sample(scored, k))
    per_unit = {}
    for unit in units:  # timestamps follow booklet order
        if unit.kind is None:
            per_unit[unit.id] = ([], LS_RH1 if unit is units[0] else LS_RH)
            continue
        if not unit.scored:
            content = [var('VIDEO', 1 if rng.random() < 2 / 3 else 1.0000066)]
            laststate = LS_VID
        else:
            value, code, score = unit.answer(unit.id in correct)
            content = [var('interact', value, 'CODING_COMPLETE', code, score), var('mainAudio', main_audio())]
            if unit.feedback:
                content.append(var('AudioFeedback', 1))
            laststate = LS_ITEM % rng.choice(['some', 'complete'])
        per_unit[unit.id] = ([{'id': 'responses', 'content': compact(content), 'ts': ts,
                               'responseType': 'iqb-standard@2.0'}], laststate)
        ts += rng.randint(850, 5300)
    rows = [[group_id, login, '', booklet_name, u, u, compact(per_unit[u][0]), per_unit[u][1]]
            for u in sorted(per_unit)]
    return rows, 100 * k / len(scored)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CONFIGS:
        raise SystemExit(f'usage: {sys.argv[0]} {"|".join(CONFIGS)}')
    name = sys.argv[1]
    cfg = CONFIGS[name]
    check_format()
    unit_ids = [u.get('id') for u in etree.parse(str(REPO / f'booklets/booklet_{name}.xml')).iter('Unit')]
    units = [Unit(cfg['units'], u, cfg['int_drop']) for u in unit_ids]
    assert units[0].kind is None, 'booklet must start with an RH unit'
    testtakers = etree.parse(str(REPO / f'testtaker/testtaker_{name}.xml'))

    shares = []
    for gi, code in enumerate(cfg['groups']):
        group_id = f'TestTakerGroup_{code}_{name}'
        group = testtakers.find(f".//Group[@id='{group_id}']")
        if group is None:
            raise SystemExit(f'{group_id} not found in testtaker_{name}.xml')
        rows = []
        logins = [login.get('name') for login in group.findall('Login')]
        for li, login in enumerate(logins):
            ts = cfg['start_ts'] + gi * 300_000_000 + li * 10_000_000 + rng.randint(1000, 3000)
            login_rows_, share = login_rows(group_id, login, f'BOOKLET_{name.upper()}', units, ts)
            rows += login_rows_
            shares.append(share)
        text = to_csv(rows)
        (HERE / f'responses_{name}_{code}.csv').write_text(text, encoding='utf-8', newline='')
        (HERE / f'responses_{name}_{code}.json').write_text(csv_to_json(text), encoding='utf-8')
        print(f'responses_{name}_{code}: {len(logins)} logins, {len(rows)} rows')
    print(f'right answers {min(shares):.1f}% .. {max(shares):.1f}%, mean {sum(shares) / len(shares):.1f}%')


if __name__ == '__main__':
    main()
