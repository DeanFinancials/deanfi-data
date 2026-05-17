#!/usr/bin/env python3
"""Validate dailycombined/market_pulse_input.json for Market Pulse publishing."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]


def load_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).with_name('market_pulse_input.schema.json')
    return json.loads(schema_path.read_text())


def collect_schema_errors(payload: Dict[str, Any]) -> List[str]:
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors: List[str] = []
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        path = '.'.join(str(part) for part in error.path)
        prefix = f'{path}: ' if path else ''
        errors.append(f'{prefix}{error.message}')
    return errors


def validate_payload(payload: Dict[str, Any]) -> ValidationResult:
    structural_errors = collect_schema_errors(payload)

    validation = payload.get('validation')
    if not isinstance(validation, dict):
        structural_errors.append('validation must be an object')
        blocking_failures: List[str] = []
        is_valid = False
    else:
        raw_failures = validation.get('blocking_failures')
        blocking_failures = [str(item) for item in raw_failures] if isinstance(raw_failures, list) else []
        is_valid = validation.get('is_valid') is True

    errors = structural_errors + blocking_failures
    if not is_valid:
        errors.append('validation.is_valid must be true')

    return ValidationResult(ok=not errors, errors=errors)


def validate_file(input_path: Path) -> ValidationResult:
    try:
        payload = json.loads(input_path.read_text())
    except FileNotFoundError:
        return ValidationResult(ok=False, errors=[f'file not found: {input_path}'])
    except json.JSONDecodeError as exc:
        return ValidationResult(ok=False, errors=[f'invalid JSON: {exc}'])

    if not isinstance(payload, dict):
        return ValidationResult(ok=False, errors=['root must be an object'])

    return validate_payload(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate Market Pulse input JSON.')
    parser.add_argument(
        'input_path',
        nargs='?',
        default=Path(__file__).with_name('market_pulse_input.json'),
        type=Path,
    )
    args = parser.parse_args()

    result = validate_file(args.input_path)
    if result.ok:
        print(f'OK: {args.input_path}')
        return 0

    print(f'FAILED: {args.input_path}')
    for error in result.errors:
        print(f'- {error}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
