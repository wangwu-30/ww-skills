#!/usr/bin/env python3
"""Prepare and audit one isolated Codex skill context; never starts a task run."""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill-name', required=True)
    p.add_argument('--skill-file', required=True, type=Path)
    p.add_argument('--auth-file', type=Path, help='Optional exact auth file to copy, usually auth.json')
    p.add_argument('--codex', default=shutil.which('codex') or 'codex')
    p.add_argument('--work-dir', type=Path, default=Path.cwd())
    p.add_argument('--audit-output', type=Path, required=True)
    p.add_argument('--prompt', default='Load the tested skill and follow it.')
    p.add_argument('--keep-home', action='store_true', help='Keep and print temporary HOME for subsequent execution')
    p.add_argument('--allowed-system-skill', action='append', default=[], metavar='NAME',
                   help='Allow an identical Codex built-in system skill; repeat for each name')
    a = p.parse_args()

    skill = a.skill_file.resolve()
    body = skill.read_text()
    home = Path(tempfile.mkdtemp(prefix='codex-skill-eval-'))
    codex_home = home / '.codex'
    target = home / '.agents' / 'skills' / a.skill_name
    codex_home.mkdir(mode=0o700)
    target.mkdir(parents=True)
    shutil.copyfile(skill, target / 'SKILL.md')
    if a.auth_file:
        auth = a.auth_file.resolve()
        shutil.copyfile(auth, codex_home / auth.name)
        os.chmod(codex_home / auth.name, 0o600)
    os.chmod(home, 0o700)
    env = os.environ.copy()
    env.update(HOME=str(home), CODEX_HOME=str(codex_home))
    cmd = [a.codex, 'debug', 'prompt-input', a.prompt + '\n\n' + body]
    proc = subprocess.run(cmd, cwd=a.work_dir, env=env, capture_output=True, text=True)
    if proc.returncode:
        raise SystemExit(f'prompt-input failed ({proc.returncode}): {proc.stderr}')
    try:
        rendered = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise SystemExit(f'prompt-input did not return JSON: {e}')
    a.audit_output.parent.mkdir(parents=True, exist_ok=True)
    a.audit_output.write_text(json.dumps(rendered, ensure_ascii=False, indent=2) + '\n')
    def texts(value):
        if isinstance(value, dict):
            return [value.get('text', '')] + sum((texts(v) for k, v in value.items() if k != 'text'), [])
        if isinstance(value, list):
            return sum((texts(v) for v in value), [])
        return []
    text = '\n'.join(texts(rendered))
    # Only explicitly named, invariant built-in skills may be present beside the
    # tested package. User/project skills remain disallowed by the audit contract.
    skill_names = []
    for marker in ('### Available skills',):
        if marker in text:
            section = text.split(marker, 1)[1].split('</skills_instructions>', 1)[0]
            for line in section.splitlines():
                stripped = line.strip()
                if stripped.startswith('- '):
                    name = stripped[2:].split(':', 1)[0].strip()
                    if name != a.skill_name and name not in a.allowed_system_skill:
                        skill_names.append(name)
    body_present = body in text
    path_present = a.skill_name in text
    report = {'home': str(home), 'codex_home': str(codex_home), 'audit_file': str(a.audit_output.resolve()),
              'command': [a.codex, 'debug', 'prompt-input', '<prompt + tested skill body>'],
              'allowed_system_skills': sorted(set(a.allowed_system_skill)),
              'other_skills': sorted(set(skill_names)), 'skill_body_present': body_present,
              'skill_path_present': path_present, 'passed': not skill_names and body_present}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if a.keep_home:
        print(f'KEEP_HOME={home}')
    if not report['passed']:
        if not a.keep_home:
            shutil.rmtree(home)
        raise SystemExit(2)
    if not a.keep_home:
        shutil.rmtree(home)


if __name__ == '__main__':
    main()
