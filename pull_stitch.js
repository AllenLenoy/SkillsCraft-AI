const fs = require('fs');
const path = require('path');

const screensData = JSON.parse(fs.readFileSync('C:/Users/allen/.gemini/antigravity-ide/brain/eda2c8d2-d582-4254-bc1e-4b64e68c1014/.system_generated/steps/70/output.txt', 'utf8'));
const projectRaw = JSON.parse(fs.readFileSync('C:/Users/allen/.gemini/antigravity-ide/brain/eda2c8d2-d582-4254-bc1e-4b64e68c1014/.system_generated/steps/53/output.txt', 'utf8'));
const craftProject = projectRaw.projects.find(p => p.name.includes('4927273723283399255'));

fs.mkdirSync('designs', { recursive: true });
fs.mkdirSync('screens', { recursive: true });

if (craftProject && craftProject.designTheme) {
  fs.writeFileSync(path.join('designs', 'DESIGN.md'), craftProject.designTheme.designMd || '');
  fs.writeFileSync(path.join('designs', 'theme-tokens.json'), JSON.stringify(craftProject.designTheme, null, 2));
  console.log('Saved designs/DESIGN.md and designs/theme-tokens.json');
}

async function downloadScreens() {
  const manifest = [];
  for (const s of screensData.screens) {
    const screenId = s.name.split('/').pop();
    const safeTitle = s.title.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
    const fileName = safeTitle + '.html';
    const filePath = path.join('screens', fileName);
    
    console.log('Downloading', s.title, '->', fileName);
    const res = await fetch(s.htmlCode.downloadUrl);
    const html = await res.text();
    fs.writeFileSync(filePath, html);
    
    manifest.push({
      id: screenId,
      title: s.title,
      file: fileName,
      width: s.width,
      height: s.height,
      deviceType: s.deviceType,
      screenshotUrl: s.screenshot?.downloadUrl
    });
  }
  
  fs.writeFileSync(path.join('screens', 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log('All screens successfully downloaded.');
}

downloadScreens().catch(err => {
  console.error('Download error:', err);
  process.exit(1);
});
