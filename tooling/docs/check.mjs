import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import MarkdownIt from 'markdown-it';
import GithubSlugger from 'github-slugger';
import { load } from 'cheerio';
import { chromium } from 'playwright';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const markdown = new MarkdownIt({ html: true });

export function inspectMarkdown(source) {
  const $ = load(markdown.render(source));
  const slugger = new GithubSlugger();
  const anchors = new Set();
  $('h1,h2,h3,h4,h5,h6').each((_, element) => {
    anchors.add(slugger.slug($(element).text()));
  });
  $('[id],a[name]').each((_, element) => {
    for (const attribute of ['id', 'name']) {
      if ($(element).attr(attribute)) anchors.add($(element).attr(attribute));
    }
  });
  const links = [];
  $('a[href],img[src]').each((_, element) => {
    links.push($(element).attr(element.tagName === 'img' ? 'src' : 'href'));
  });
  const diagrams = markdown.parse(source, {}).filter(
    token => token.type === 'fence' && token.info.trim().split(/\s+/)[0] === 'mermaid',
  ).map(token => ({ code: token.content, line: token.map[0] + 1 }));
  return { anchors, links, diagrams };
}

function inside(root, target) {
  const relative = path.relative(root, target);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

export async function checkDocuments(root, files) {
  root = await fs.realpath(root);
  const documents = new Map();
  const errors = [];
  async function read(file) {
    if (!documents.has(file)) documents.set(file, inspectMarkdown(await fs.readFile(file, 'utf8')));
    return documents.get(file);
  }
  const diagrams = [];
  for (const file of files) {
    const sourcePath = path.resolve(root, file);
    if (!inside(root, sourcePath)) throw new Error(`Source outside repository: ${file}`);
    const document = await read(sourcePath); // A missing requested source must fail.
    diagrams.push(...document.diagrams.map(diagram => ({ ...diagram, file })));
    for (const target of document.links) {
      // Remote URLs and protocol-relative URLs are deliberately offline checks' limit.
      if (/^[a-z][a-z\d+.-]*:/i.test(target) || target.startsWith('//')) continue;
      try {
        const hash = target.indexOf('#');
        const rawPath = hash < 0 ? target : target.slice(0, hash);
        const fragment = hash < 0 ? '' : target.slice(hash + 1);
        const pathname = decodeURIComponent(rawPath.split('?')[0]);
        const destination = pathname.startsWith('/')
          ? path.resolve(root, `.${pathname}`)
          : path.resolve(path.dirname(sourcePath), pathname || path.basename(sourcePath));
        if (!inside(root, destination) || !inside(root, await fs.realpath(destination))) {
          throw new Error('destination escapes repository');
        }
        const stat = await fs.stat(destination);
        if (fragment) {
          if (!stat.isFile()) throw new Error('fragment targets a directory');
          if (/\.md$/i.test(destination)) {
            const anchor = decodeURIComponent(fragment);
            if (!(await read(destination)).anchors.has(anchor)) throw new Error(`missing anchor #${anchor}`);
          } else {
            throw new Error('fragment on non-Markdown target is unsupported');
          }
        }
      } catch (error) {
        errors.push(`${file}: ${target}: ${error.message}`);
      }
    }
  }
  return { errors, diagrams };
}

export async function renderDiagrams(diagrams, output) {
  // Serve only bundled Mermaid assets into an isolated page. No document HTML,
  // scripts, remote images, or diagram click handlers are executed from Markdown.
  const dist = path.join(here, 'node_modules/mermaid/dist');
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  const previews = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, serviceWorkers: 'block' });
    await context.route('**/*', async route => {
      const url = new URL(route.request().url());
      const asset = path.resolve(dist, `.${decodeURIComponent(url.pathname)}`);
      if (url.origin !== 'http://mermaid.local' || !inside(dist, asset) || !asset.endsWith('.mjs')) {
        await route.abort();
        return;
      }
      try {
        await route.fulfill({ body: await fs.readFile(asset), contentType: 'text/javascript' });
      } catch {
        await route.abort();
      }
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30_000);
    await page.setContent('<html><body><div id="drawing"></div></body></html>');
    await page.addScriptTag({ type: 'module', content: `
      import mermaid from 'http://mermaid.local/mermaid.esm.min.mjs';
      mermaid.initialize({startOnLoad: false, securityLevel: 'strict', theme: 'default'});
      window.mermaidReady = mermaid;
    ` });
    await page.waitForFunction(() => window.mermaidReady);
    for (const [index, diagram] of diagrams.entries()) {
      const name = `diagram-${index + 1}`;
      await fs.writeFile(path.join(output, `${name}.mmd`), diagram.code);
      try {
        const svg = await page.evaluate(async ({ code, id }) => {
          await window.mermaidReady.parse(code);
          const result = await window.mermaidReady.render(id, code);
          document.querySelector('#drawing').innerHTML = result.svg;
          return result.svg;
        }, { code: diagram.code, id: name });
        await fs.writeFile(path.join(output, `${name}.svg`), svg);
        await page.locator('#drawing svg').screenshot({ path: path.join(output, `${name}.png`) });
        previews.push({ ...diagram, name });
      } catch (error) {
        errors.push(`${diagram.file}:${diagram.line}: Mermaid: ${error.message}`);
      }
    }
  } finally {
    await browser.close();
  }
  await fs.writeFile(path.join(output, 'sources.json'), JSON.stringify(diagrams, null, 2));
  // Markdown source remains text; only generated filenames enter the preview links.
  await fs.writeFile(path.join(output, 'index.md'), previews.map(d =>
    `### ${d.file}:${d.line}\n\n![Diagram](${d.name}.png)\n\n[SVG](${d.name}.svg) · [Source](${d.name}.mmd)\n`,
  ).join('\n'));
  return errors;
}

async function main() {
  const files = process.argv.slice(2);
  if (!files.length) throw new Error('Provide repository-relative Markdown source paths');
  const result = await checkDocuments(repo, files);
  const outputRoot = path.join(here, 'previews');
  await fs.mkdir(outputRoot, { recursive: true });
  const output = await fs.mkdtemp(path.join(outputRoot, 'run-'));
  result.errors.push(...await renderDiagrams(result.diagrams, output));
  await fs.writeFile(path.join(output, 'result.json'), JSON.stringify({ files, errors: result.errors }, null, 2));
  console.log(`Documentation previews: ${output}`);
  if (result.errors.length) throw new Error(result.errors.join('\n'));
  console.log('Local links, Markdown anchors and Mermaid renders passed for the requested sources.');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
