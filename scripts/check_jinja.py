#!/usr/bin/env python3
"""
Lightweight Jinja template syntax checker.
Usage: python scripts/check_jinja.py --path templates

- Walks `templates/` and tries to parse each file with Jinja's parser.
- Exits non-zero if any syntax errors are found.

This script is local-only and has no network or git effects.
"""
import sys
import os
import argparse

try:
    from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
except Exception as e:
    print("Missing dependency: jinja2 is required. Install with: pip install Jinja2")
    sys.exit(2)


def find_templates(path, exts):
    for root, dirs, files in os.walk(path):
        for f in files:
            if any(f.lower().endswith(e) for e in exts):
                yield os.path.join(root, f)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Check Jinja templates for syntax errors")
    p.add_argument("--path", default="templates", help="Templates root folder (default: templates)")
    p.add_argument("--ext", action="append", help="File extension to check (may be given multiple times). Defaults: .html, .htm, .j2, .jinja",)
    args = p.parse_args(argv)

    exts = args.ext if args.ext else [".html", ".htm", ".j2", ".jinja"]

    tpl_root = os.path.abspath(args.path)
    if not os.path.isdir(tpl_root):
        print(f"Templates path not found: {tpl_root}")
        return 2

    env = Environment(loader=FileSystemLoader(tpl_root))

    errors = []
    for tpl_path in find_templates(tpl_root, exts):
        rel = os.path.relpath(tpl_path, tpl_root)
        try:
            src = open(tpl_path, encoding="utf-8").read()
            # parse only (no template rendering)
            env.parse(src)
        except TemplateSyntaxError as e:
            print(f"SYNTAX ERROR: {rel}:{e.lineno}: {e.message}")
            errors.append((rel, e))
        except Exception as e:
            print(f"ERROR: {rel}: {e}")
            errors.append((rel, e))

    if errors:
        print(f"\nFound {len(errors)} template error(s). Fix before continuing.")
        return 2

    print("OK: No Jinja syntax errors found.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
