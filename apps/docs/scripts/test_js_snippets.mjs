import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

// Fix for __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FILES_TO_TEST = [
  'apps/docs/docs/get-started/api.mdx'
];

async function run() {
  const rootDir = path.resolve(__dirname, '../../..');
  let failures = 0;
  let total = 0;

  for (const relPath of FILES_TO_TEST) {
    const filePath = path.join(rootDir, relPath);
    if (!fs.existsSync(filePath)) {
      console.error(`File not found: ${filePath}`);
      continue;
    }

    console.log(`Processing ${relPath}...`);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // Regex for js/ts blocks, allowing for indentation and CRLF
    const regex = /^\s*```(?:js|javascript|ts|typescript)[ \t]*\r?\n([\s\S]*?)\r?\n\s*```/gm;
    let match;
    let index = 0;

    while ((match = regex.exec(content)) !== null) {
      index++;
      total++;
      const code = match[1];
      
      let runnableCode = code;
      
      if (code.includes('DEVELOPER_API_KEY')) {
          if (process.env.DEVELOPER_API_KEY) {
              runnableCode = `const DEVELOPER_API_KEY = "${process.env.DEVELOPER_API_KEY}";\n` + runnableCode;
          } else {
               // Mock if valid key not present, just to check syntax/runtime imports
              console.log(`Warning: DEVELOPER_API_KEY not set. Mocking it for block ${index}.`);
              runnableCode = `const DEVELOPER_API_KEY = "mock_key";\n` + runnableCode;
          }
      }

      // Wrap in async IIFE
      runnableCode = `(async () => {\n${runnableCode}\n})();`;

      const tempFile = path.join(__dirname, `temp_${index}.mjs`);
      fs.writeFileSync(tempFile, runnableCode);

      try {
        console.log(`Running block ${index}...`);
        execSync(`node ${tempFile}`, { stdio: 'inherit' });
        console.log(`Block ${index} passed.`);
      } catch (e) {
        console.error(`Block ${index} failed.`);
        failures++;
      } finally {
        if (fs.existsSync(tempFile)) fs.unlinkSync(tempFile);
      }
    }
  }

  console.log(`\nTest Summary: ${total - failures}/${total} blocks passed.`);
  if (failures > 0) process.exit(1);
}

run().catch(e => {
  console.error(e);
  process.exit(1);
});
