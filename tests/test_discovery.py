"""Opt-in native discovery integration when the Codex CLI is installed."""
from pathlib import Path
import unittest

from agentctl import harnesses
from agentctl.common import Refused, execute
from test_runner import GitFixture


class NativeDiscoveryTests(GitFixture):
    def test_root_nested_worktree_and_external_skill_alias(self):
        try:
            harnesses.binary('codex')
        except Refused as error:
            self.skipTest(str(error))
        def skill(root, name):
            directory = root / name
            directory.mkdir(parents=True)
            (directory / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Native discovery acceptance fixture.\n---\nRead this fixture only when requested.\n')
            return directory
        skill(self.repository / '.agents/skills', 'matrix-root')
        nested = self.repository / 'nested'
        skill(nested / '.agents/skills', 'matrix-nested')
        external = skill(self.root / 'external', 'matrix-alias')
        (self.repository / '.agents/skills/alias').symlink_to(external, target_is_directory=True)
        execute(['git','add','.'], cwd=self.repository)
        execute(['git','commit','-m','discovery fixtures'], cwd=self.repository)
        worktree = self.root / 'worktree'
        execute(['git','worktree','add','-b','codex/discovery',str(worktree)], cwd=self.repository)
        for cwd, expected in [(self.repository, {'matrix-root','matrix-alias'}),
                              (nested, {'matrix-root','matrix-alias','matrix-nested'}),
                              (worktree / 'nested', {'matrix-root','matrix-alias','matrix-nested'})]:
            catalog = harnesses.skill_catalog(cwd)
            actual = {s['name'] for entry in catalog for s in entry['skills'] if s['enabled']}
            self.assertTrue(expected <= actual, (str(cwd), expected - actual))
