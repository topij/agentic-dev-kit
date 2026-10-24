import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { checkDocuments, inspectMarkdown, renderDiagrams } from './check.mjs';

async function fixture(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'devkit-docs-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  await fs.mkdir(path.join(root, 'docs'));
  await fs.writeFile(path.join(root, 'docs/target.md'), '# Héllo `world`!\n\n## Repeat\n\n## Repeat\n\nExplicit\n----\n\n<a id="custom"></a>\n');
  return root;
}

test('inline, reference, HTML and image destinations; GitHub heading slugs', async t => {
  const root = await fixture(t);
  await fs.writeFile(path.join(root, 'docs/picture.svg'), '<svg/>');
  await fs.writeFile(path.join(root, 'README.md'), `# Home
[inline](docs/target.md#h%C3%A9llo-world)
[reference][target]

[target]: docs/target.md#repeat-1
<a href="docs/target.md#custom">html</a>
![image](docs/picture.svg)
[setext](docs/target.md#explicit)
[same](#home)
[external](https://example.invalid/no-network)
\`[not a link](missing)\`
\`\`\`md
[example](missing)
# Not a heading
\`\`\`
`);
  assert.deepEqual((await checkDocuments(root, ['README.md'])).errors, []);
});

test('broken files, anchors, images and escapes fail with source context', async t => {
  const root = await fixture(t);
  await fs.symlink(os.tmpdir(), path.join(root, 'outside'));
  const targets = ['docs/missing.md', 'docs/target.md#absent', 'docs/#heading', '../escape', 'outside/', 'docs/target.md#repeat-2', 'docs/target.md#repeat#extra'];
  for (const target of targets) {
    await fs.writeFile(path.join(root, 'README.md'), `[broken](${target})`);
    const result = await checkDocuments(root, ['README.md']);
    assert.equal(result.errors.length, 1, target);
    assert.match(result.errors[0], /^README.md:/);
  }
  await fs.writeFile(path.join(root, 'README.md'), '[reference][target]\n\n[target]: docs/target.md#absent');
  assert.equal((await checkDocuments(root, ['README.md'])).errors.length, 1);
  await fs.writeFile(path.join(root, 'README.md'), '![missing](image.png)');
  assert.equal((await checkDocuments(root, ['README.md'])).errors.length, 1);
  await assert.rejects(checkDocuments(root, ['missing.md']), /ENOENT/);
});

test('only real Mermaid fences become renders', () => {
  const source = '# Topic\n\n````markdown\n```mermaid\ninvalid\n```\n````\n\n~~~mermaid\nflowchart LR\nA-->B\n~~~\n';
  const result = inspectMarkdown(source);
  assert.deepEqual([...result.anchors], ['topic']);
  assert.deepEqual(result.diagrams, [{ code: 'flowchart LR\nA-->B\n', line: 9 }]);
});

test('browser renders previews, rejects malformed Mermaid and retains source evidence', async t => {
  const root = await fixture(t);
  const result = await renderDiagrams([
    { file: 'good.md', line: 1, code: 'flowchart LR\nA[Start]-->B[Finish]' },
    { file: 'bad.md', line: 4, code: 'flowchart LR\nA[Unclosed' },
  ], root);
  assert.equal(result.length, 1);
  assert.match(result[0], /^bad.md:4: Mermaid:/);
  assert.match(await fs.readFile(path.join(root, 'diagram-1.svg'), 'utf8'), /<svg/);
  assert.ok((await fs.stat(path.join(root, 'diagram-1.png'))).size > 0);
  assert.match(await fs.readFile(path.join(root, 'diagram-2.mmd'), 'utf8'), /Unclosed/);
});
