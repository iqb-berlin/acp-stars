# Notes

## testtaker_sp2g.xml

Created from `testtaker_sp1g.xml`: same groups, login names and passwords (141 logins in 9 groups), booklet changed to `booklet_sp2g`. The sp1g column below shows the current state, after the removal described in the next section.

Three logins were moved to a different group:

| Login      | From group             | To group               |
|------------|------------------------|------------------------|
| `7ttgf_22` | `TestTakerGroup_7ttgf` | `TestTakerGroup_yqhsj` |
| `ldk82_3`  | `TestTakerGroup_ldk82` | `TestTakerGroup_vdvl1` |
| `ldk82_6`  | `TestTakerGroup_ldk82` | `TestTakerGroup_vdvl1` |

Resulting group sizes:

| Group                  | sp1g | sp2g |
|------------------------|-----:|-----:|
| `TestTakerGroup_a5u4x` |    4 |    4 |
| `TestTakerGroup_a8x9e` |   15 |   15 |
| `TestTakerGroup_8uxhm` |   15 |   15 |
| `TestTakerGroup_ldk82` |   15 |   13 |
| `TestTakerGroup_gazul` |   17 |   18 |
| `TestTakerGroup_7ttgf` |   25 |   24 |
| `TestTakerGroup_vdvl1` |   18 |   21 |
| `TestTakerGroup_gp0wz` |   15 |   15 |
| `TestTakerGroup_yqhsj` |   15 |   16 |
| **Total**              |  139 |  141 |

sp1g and sp2g share all login names, so they must be used in separate Testcenter workspaces.

## testtaker_sp1g.xml

Two logins were removed (after `testtaker_sp2g.xml` had been created, so they still exist there):

| Login      | Group                  |
|------------|------------------------|
| `vdvl1_15` | `TestTakerGroup_vdvl1` |
| `gazul_15` | `TestTakerGroup_gazul` |

## testtaker_ma1g.xml / testtaker_ma2g.xml

- `testtaker_ma1g.xml` was replaced by a copy of `testtaker_sp1g.xml` (139 logins), booklet `booklet_ma1g`. The old logins `schlummer` and `9283982772883777483838` are gone.
- `testtaker_ma2g.xml` is new, a copy of `testtaker_sp2g.xml` (141 logins, incl. the three moved logins and `vdvl1_15` / `gazul_15`), booklet `booklet_ma2g`.
- Groups and logins are identical to the sp counterparts, so ma1g/sp1g and ma2g/sp2g must be used in separate Testcenter workspaces.

## Group IDs

All group IDs now end with the name of their testtaker file, e.g. `TestTakerGroup_a5u4x` became `TestTakerGroup_a5u4x_sp1g` in `testtaker_sp1g.xml` and `TestTakerGroup_a5u4x_ma2g` in `testtaker_ma2g.xml`. This applies to all six files (`_sp1g`, `_sp2g`, `_ma1g`, `_ma2g`, `_sp1et`, `_ma1et`). Group IDs are now unique across all files; login names are unchanged. The tables above use the group IDs without suffix.

## testtaker_sp1et.xml / testtaker_ma1et.xml

All 9 groups and 139 logins from `testtaker_sp1g.xml` / `testtaker_ma1g.xml` were appended to the ET files, after the existing single-login group (`d4f6z` in sp1et, `r2a3f` in ma1et). Group IDs end with `_sp1et` / `_ma1et`, booklets are `booklet_sp1et` / `booklet_ma1et`. Each ET file now has 10 groups and 140 logins. The logins share their names with sp1g/ma1g, so ET and group files must be used in separate Testcenter workspaces.

## tests/

The `groupname` in all response/log files in `tests/` (CSV and JSON) got the same suffix as the testtaker files, taken from the booklet of each file, e.g. `TestTakerGroup_a5u4x` → `TestTakerGroup_a5u4x_sp1g`, `TestTakerGroup_q9r4q` → `TestTakerGroup_q9r4q_sp1et`, `akow93j9js5f7u` → `akow93j9js5f7u_ma1g`. File names are unchanged. The ma1g group `akow93j9js5f7u_ma1g` (login `schlummer`) no longer exists in `testtaker_ma1g.xml`.

## tests/ – new sp1g response data

Generated dummy response reports (`responses_sp1g_<code>.csv` + `.json`) for the five new sp1g groups, using their current logins in `testtaker_sp1g.xml`: gazul (17), 7ttgf (25), vdvl1 (18), gp0wz (15), yqhsj (15), 90 logins in total. The existing files (a5u4x, a8x9e, 8uxhm, ldk82) are unchanged.

- Same structure as the generated files 8uxhm/a8x9e/ldk82: 80 rows per login (one per unit of `booklet_sp1g`, sorted by unit name), 67 scored `interact` responses, `mainAudio`, `AudioFeedback` on practice units, `VIDEO` on videos, no responses on RH units.
- Correct answers: `"1"` (vfauvertical), `"110000"` (but_multi_2row), `1` (dnd_Koffer); wrong answers are random other values. `code` = `score`.
- Each login gets a random share of right answers between 35% and 90% (actual: 35.8% – 89.6%, mean 62.2%).
- Timestamps increase in the order of the new `booklet_sp1g`, 0.85–5.3 s per unit, logins 10,000 s apart, groups starting at 1785200000000 and 300,000 s apart.
- The JSON files are converted from the CSV in the same way as the existing ones (conversion checked byte-for-byte against `responses_sp1g_8uxhm.json`).
- Generator: `tests/generate_responses.py sp1g`. A rerun overwrites these five groups with new random data.

## tests/ – new ma1g response data

Generated `responses_ma1g_<code>.csv` + `.json` for all 9 groups of `testtaker_ma1g.xml` (a5u4x, a8x9e, 8uxhm, ldk82, gazul, 7ttgf, vdvl1, gp0wz, yqhsj; 139 logins) with `python3 tests/generate_responses.py ma1g`. The old `responses_ma1g_akow93j9js5f7u.*` (old booklet, old group) is unchanged.

- 72 rows per login (units of the new `booklet_ma1g`), 61 scored `interact` responses; AudioFeedback on the practice units whose .voud defines audio feedback.
- Right answers are read from the `variableInfo` in each unit's .voud:
  `"3"` leftpic_scpic, `"4"` leftpic_scpic_UE, `"2"` twochoiceonly_rl, squarepic_4scrow83, toppic_4scrow350, `"1"` vierfelderAudio_Row, vfauvertical_UE, blitzsehen, dnd_Muscheln, `"3"` squarepic_4scrow400, but_row_audio_MK.
- forms_1/forms_2 use partial credit (SUM_CHAR_MATCHES against `"011000"`, code = score = matching characters 0–6). Only `"011000"` (score 6) counts as right; wrong answers are random other 6-character 0/1 strings with their matching score.
- dnd_Muscheln reports the dropped option as string `"1"`–`"4"`, like the old ma1g data.
- Share of right answers per login: 36.1% – 88.5%.
- Timestamps start at 1787000000000 (groups 300,000 s apart, logins 10,000 s apart).
- The generator now reads right answers, option counts and audio feedback from the .voud files for both booklets (`sp1g` and `ma1g`); the sp1g output keeps the same structure as before (checked against the existing data).

## scales/ – evaluation mock updated to the response-analyser-api spec

`tests/generate_evaluations.py` now mocks the `EvaluationOutput` of `evaluateResponses` as defined in https://github.com/iqb-specifications/response-analyser-api (`api.yaml`, commit 600a5f7) and writes to `scales/` (before: `tests/evaluate/`); only the `scales/responses_*` folders are replaced.

- `codedResponses[]`: `{unitAlias, responses}` — `unitId` removed (not allowed by the spec).
- `itemValues[]`: `{id, code, score}` — `value` replaced by `code` and `score`.
- `scaleValues[]`: `{scaleId, status, value}` — `assessmentPartId` removed, `status` added. A scale with at least one item value is reported: `VALID` with value, or `INSUFFICIENT_SOURCE` without value if it has fewer items than `minItemNumber`.
- Regenerated for all 9 sp1g groups (139 files, incl. the 5 new groups). All files validate against `EvaluationOutput`. For the 4 existing groups only the format changed, item scores and scale values are identical.
- ma1g and sp1et reports are still skipped (no item definitions / no instrument in `stars.json`).
- Recorded data `a5u4x_1` has 11 vfauvertical items with code 1 but score 0; this is passed through as reported.

## stars.json – ma1 items

Added `<unitId>.interact` items (`useUnitAliasAsPrefix: false`, `sourceVariable: interact`) to the 61 ma1 units whose .voud defines an `interact` variable, same rule as sp1/sp2/ma2. RH units, videos and the player entries have no items. ma1 still has no `baseScales`. `stars.json` validates against acp-index 0.6.
