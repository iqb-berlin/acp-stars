#!/usr/bin/env python3
"""Build dummy EvaluationOutput files for the IQB ResponseAnalyser endpoint.

Mocks the EvaluationOutput of evaluateResponses (POST /{workspaceId}/evaluate)
in https://github.com/iqb-specifications/response-analyser-api (api.yaml),
using the testcenter response reports in this directory plus the item and
scale definitions in ../stars.json.

One folder per response report, one JSON file per testtaker/login inside it:

    scales/<report name>/<loginname>.json

Conventions (agreed with the maintainer):
  * codedResponses  - per unit {unitAlias, responses}: the responses as
                      reported by the testcenter; they are already coded
                      (status CODING_COMPLETE with code/score), so nothing is
                      recoded here. Responses still on status VALUE_CHANGED
                      are dropped: they are player telemetry (mainAudio,
                      VIDEO, AudioFeedback), never coded results. Units left
                      without any response are dropped too, since
                      `responses` requires minItems 1.
  * itemValues      - {id, code, score}, one per unit item whose
                      sourceVariable has a coded response with a score.
                      Items without one (e.g. the vid_* units, which only
                      ever return VIDEO) are omitted.
  * scaleValues     - ScaleResult {scaleId, status, value}. A base scale is
                      reported as soon as at least one of its items has an
                      item value. With at least minItemNumber items it is
                      VALID; for method SCORE_RATIO the value is the sum of
                      the available item scores as a percentage of maxValue,
                      rounded to a whole number. With fewer it is
                      INSUFFICIENT_SOURCE and has no value.

Order matters and is deliberate: the VALUE_CHANGED responses are dropped
FIRST, and itemValues/scaleValues are then derived from what remains. So a
source variable that arrives uncoded yields no item value at all, which in
turn can push a scale below its minItemNumber and drop it. That the two are
unaffected by the filter in the current reports is a property of this data
(no VALUE_CHANGED response is any unit's sourceVariable), not of the pipeline.

Reports whose units carry no item definitions in stars.json (ma1g, sp1et) are
skipped entirely.
"""

import json
import shutil
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PACKAGE = TESTS_DIR.parent / "stars.json"
OUT_DIR = TESTS_DIR.parent / "scales"

MISSING = None  # omit rather than emit a missing code

# Uncoded telemetry; carried by the report but not part of an evaluation.
DROPPED_STATUS = "VALUE_CHANGED"


def load_package(path):
    """Map every assessment part to its item and scale definitions."""
    package = json.loads(path.read_text(encoding="utf-8"))
    parts = {}
    for part in package["assessmentParts"]:
        items = {
            unit["id"]: unit["items"]
            for unit in part["units"]
            if unit.get("items")
        }
        booklets = {
            # ./booklets/booklet_sp1g.xml -> the report's BOOKLET_SP1G
            "BOOKLET_" + Path(booklet["definitionId"]).stem.removeprefix("booklet_").upper()
            for instrument in part.get("instruments", [])
            for booklet in instrument.get("testcenterBooklet", [])
        }
        parts[part["id"]] = {
            "items": items,
            "scales": part.get("baseScales", []),
            "booklets": booklets,
        }
    return parts


def part_of_booklet(bookletname, parts):
    """BOOKLET_SP1G -> sp1, via the instruments' booklet definitions.

    Only parts that actually define items qualify: a report we cannot resolve
    to items and scales would yield nothing but codedResponses.
    """
    for part_id, part in parts.items():
        if bookletname in part["booklets"] and part["items"]:
            return part_id
    return None


def item_id(unit_id, unit_alias, definition):
    if definition.get("useUnitAliasAsPrefix", True):
        return f"{unit_alias or unit_id}.{definition['id']}"
    return definition["id"]


def coded_responses(rows):
    """Unwrap the testcenter chunks into per-unit variable-level responses."""
    units = []
    for row in rows:
        variables = []
        for chunk in row["responses"]:
            variables.extend(
                response
                for response in json.loads(chunk["content"])
                if response.get("status") != DROPPED_STATUS
            )
        if not variables:  # `responses` requires minItems 1
            continue
        units.append(
            {
                "unitAlias": row["unitname"],
                "responses": variables,
            }
        )
    return units


def item_values(units, definitions):
    values = []
    for unit in units:
        for definition in definitions.get(unit["unitAlias"], []):
            source = definition["sourceVariable"]
            response = next(
                (
                    response
                    for response in unit["responses"]
                    if response.get("id") == source and response.get("score") is not None
                ),
                MISSING,
            )
            if response is MISSING:
                continue
            values.append(
                {
                    "id": item_id(unit["unitAlias"], unit["unitAlias"], definition),
                    "code": int(response["code"]),
                    "score": int(response["score"]),
                }
            )
    return values


def percent(total, max_value):
    """Round half up, so 7/15 is 47 rather than the banker's-rounding 46."""
    return int(total * 200 // max_value + 1) // 2


def scale_values(scales, values):
    by_id = {value["id"]: value["score"] for value in values}
    result = []
    for scale in scales:
        if scale["method"] != "SCORE_RATIO":
            raise NotImplementedError(
                f"scale {scale['id']}: unsupported method {scale['method']}"
            )
        available = [
            by_id[item["id"]] for item in scale["items"] if item["id"] in by_id
        ]
        if not available:  # no item of the scale present: not relevant
            continue
        if len(available) < scale.get("minItemNumber", 0):
            result.append({"scaleId": scale["id"], "status": "INSUFFICIENT_SOURCE"})
            continue
        result.append(
            {
                "scaleId": scale["id"],
                "status": "VALID",
                "value": percent(sum(available), scale["methodParameters"]["maxValue"]),
            }
        )
    return result


def main():
    parts = load_package(PACKAGE)
    for old in OUT_DIR.glob("responses_*"):
        shutil.rmtree(old)

    for report in sorted(TESTS_DIR.glob("responses_*.json")):
        rows = json.loads(report.read_text(encoding="utf-8"))
        booklets = {row["bookletname"] for row in rows}
        if len(booklets) != 1:
            raise ValueError(f"{report.name}: expected one booklet, got {booklets}")
        part_id = part_of_booklet(booklets.pop(), parts)
        if part_id is None:
            print(f"{report.name}: no item definitions for its units, skipped")
            continue
        part = parts[part_id]

        by_login = {}
        for row in rows:
            by_login.setdefault(row["loginname"], []).append(row)

        folder = OUT_DIR / report.stem
        folder.mkdir(parents=True)
        for login, login_rows in sorted(by_login.items()):
            units = coded_responses(login_rows)
            values = item_values(units, part["items"])
            output = {
                "codedResponses": units,
                "itemValues": values,
                "scaleValues": scale_values(part["scales"], values),
            }
            target = folder / f"{login}.json"
            target.write_text(
                json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            f"{report.name}: {part_id}, {len(by_login)} testtakers -> "
            f"{folder.relative_to(TESTS_DIR.parent)}/"
        )


if __name__ == "__main__":
    main()
