const fs = require('fs');
const path = require('path');

const manifestPath = 'c:/Users/allen/OneDrive/Desktop/skillscraft/screens/manifest.json';
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

const targetDir1 = 'c:/Users/allen/OneDrive/Desktop/skillscraft/screens/screenshots';
const targetDir2 = 'C:/Users/allen/.gemini/antigravity-ide/brain/eda2c8d2-d582-4254-bc1e-4b64e68c1014';

fs.mkdirSync(targetDir1, { recursive: true });
fs.mkdirSync(targetDir2, { recursive: true });

async function downloadAll() {
  for (const item of manifest) {
    if (!item.screenshotUrl) continue;
    
    const safeName = item.title.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase() + '.png';
    const file1 = path.join(targetDir1, safeName);
    const file2 = path.join(targetDir2, safeName);
    
    console.log('Downloading screenshot for:', item.title);
    const res = await fetch(item.screenshotUrl);
    const buffer = Buffer.from(await res.arrayBuffer());
    
    fs.writeFileSync(file1, buffer);
    fs.writeFileSync(file2, buffer);
    console.log('Saved to', safeName);
  }
  console.log('All screenshots downloaded successfully.');
}

downloadAll().catch(e => {
  console.error(e);
  process.exit(1);
});
