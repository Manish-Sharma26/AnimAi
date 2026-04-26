const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const REPORT_PATH = path.join(__dirname, 'PROJECT_REPORT.md');
const OUT_DIR = path.join(__dirname, 'diagrams');

// Create output directory
if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR);

const content = fs.readFileSync(REPORT_PATH, 'utf8');

// Extract section heading + mermaid block pairs
const HEADING_RE = /^###\s+(.+)$/gm;
const BLOCK_RE = /```mermaid\n([\s\S]*?)```/g;

// Build list of headings and their positions
const headings = [];
let hm;
while ((hm = HEADING_RE.exec(content)) !== null) {
  headings.push({ pos: hm.index, title: hm[1].trim() });
}

// Build list of mermaid blocks and their positions
const blocks = [];
let bm;
while ((bm = BLOCK_RE.exec(content)) !== null) {
  blocks.push({ pos: bm.index, code: bm[1].trim() });
}

// Mermaid init config for Word-ready output: large font, clean theme
const INIT = `%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "20px",
    "fontFamily": "Arial, sans-serif",
    "primaryColor": "#dbeafe",
    "primaryTextColor": "#1e3a5f",
    "primaryBorderColor": "#3b82f6",
    "lineColor": "#475569",
    "secondaryColor": "#dcfce7",
    "tertiaryColor": "#fef9c3"
  }
}}%%
`;

let diagramCount = 0;

blocks.forEach((block, i) => {
  // Find the closest heading BEFORE this block
  let heading = `diagram_${i + 1}`;
  for (const h of headings) {
    if (h.pos < block.pos) heading = h.title;
    else break;
  }

  // Sanitize heading for filename
  const safeName = heading
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .substring(0, 60)
    .toLowerCase();

  const filename = `${String(i + 1).padStart(2, '0')}_${safeName}`;
  const mmdPath = path.join(OUT_DIR, `${filename}.mmd`);
  const pngPath = path.join(OUT_DIR, `${filename}.png`);

  // Prepend init config (skip if already has one)
  const codeWithInit = block.code.startsWith('%%{')
    ? block.code
    : INIT + block.code;

  fs.writeFileSync(mmdPath, codeWithInit, 'utf8');

  console.log(`[${i + 1}] Exporting: ${filename}.png`);

  try {
    execSync(
      `mmdc -i "${mmdPath}" -o "${pngPath}" -w 2400 -s 2 --backgroundColor white`,
      { stdio: 'inherit' }
    );
    diagramCount++;
  } catch (e) {
    console.error(`  ❌ Failed: ${e.message}`);
  }
});

console.log(`\n✅ Done! ${diagramCount} diagram(s) exported to: ${OUT_DIR}`);
console.log('→ Open the "diagrams" folder and insert the PNGs into your Word document.');
