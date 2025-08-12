#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Custom schema documentation generator
 * Addresses specific issues with generic tools:
 * - Eliminates "Untitled/Unknown" labels
 * - Properly handles arrays and nested objects
 * - Focuses on useful documentation for humans
 */

const SCHEMA_PATH = 'apps/hasura-clickhouse/oso_subgraph/connector/oso_clickhouse/configuration.schema.json';
const OUTPUT_DIR = 'docs/schema-docs';
const OUTPUT_FILE = 'configuration-schema.md';

function generateDocumentation(schema, title = 'Configuration Schema') {
  let markdown = `# ${title}\n\n`;
  
  if (schema.description) {
    markdown += `${schema.description}\n\n`;
  }

  markdown += `## Properties\n\n`;
  markdown += generateProperties(schema.properties || {}, schema.required || []);
  
  return markdown;
}

function generateProperties(properties, required = [], level = 0) {
  let markdown = '';
  const indent = '  '.repeat(level);
  
  for (const [propName, propSchema] of Object.entries(properties)) {
    const isRequired = required.includes(propName);
    const requiredBadge = isRequired ? ' **Required**' : '';
    
    markdown += `${indent}- **\`${propName}\`**${requiredBadge}\n`;
    
    if (propSchema.description) {
      markdown += `${indent}  ${propSchema.description}\n`;
    }
    
    // Handle type information
    const typeInfo = getTypeInfo(propSchema);
    if (typeInfo) {
      markdown += `${indent}  - Type: \`${typeInfo}\`\n`;
    }
    
    // Handle default values
    if (propSchema.default !== undefined) {
      markdown += `${indent}  - Default: \`${JSON.stringify(propSchema.default)}\`\n`;
    }
    
    // Handle examples
    if (propSchema.examples && propSchema.examples.length > 0) {
      markdown += `${indent}  - Example: \`${JSON.stringify(propSchema.examples[0])}\`\n`;
    }
    
    // Handle nested objects (but not primitive arrays)
    if (propSchema.type === 'object' && propSchema.properties) {
      markdown += `${indent}  - Properties:\n`;
      markdown += generateProperties(propSchema.properties, propSchema.required || [], level + 2);
    }
    
    // Handle arrays of objects (skip primitive arrays)
    if (propSchema.type === 'array' && propSchema.items?.type === 'object' && propSchema.items.properties) {
      markdown += `${indent}  - Array items have properties:\n`;
      markdown += generateProperties(propSchema.items.properties, propSchema.items.required || [], level + 2);
    }
    
    markdown += '\n';
  }
  
  return markdown;
}

function getTypeInfo(schema) {
  if (schema.type) {
    if (schema.type === 'array' && schema.items) {
      if (schema.items.type) {
        return `array of ${schema.items.type}`;
      } else if (schema.items.properties) {
        return 'array of objects';
      }
      return 'array';
    }
    return schema.type;
  }
  
  if (schema.enum) {
    return `enum: ${schema.enum.map(v => `"${v}"`).join(' | ')}`;
  }
  
  if (schema.$ref) {
    return `reference: ${schema.$ref}`;
  }
  
  return 'mixed';
}

function main() {
  try {
    // Read the schema file
    console.log(`Reading schema from: ${SCHEMA_PATH}`);
    const schemaContent = fs.readFileSync(SCHEMA_PATH, 'utf8');
    const schema = JSON.parse(schemaContent);
    
    // Generate documentation
    console.log('Generating documentation...');
    const documentation = generateDocumentation(schema, 'OSO Clickhouse Configuration Schema');
    
    // Ensure output directory exists
    if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
      console.log(`Created output directory: ${OUTPUT_DIR}`);
    }
    
    // Write documentation
    const outputPath = path.join(OUTPUT_DIR, OUTPUT_FILE);
    fs.writeFileSync(outputPath, documentation);
    
    console.log(`✅ Documentation generated successfully: ${outputPath}`);
    console.log(`📄 Generated ${documentation.split('\n').length} lines of documentation`);
    
  } catch (error) {
    console.error('❌ Error generating documentation:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { generateDocumentation, generateProperties, getTypeInfo };
