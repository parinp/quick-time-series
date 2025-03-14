const fs = require('fs');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('=== Supabase Environment Setup ===');
console.log('This script will help you set up your Supabase credentials for the Time Series Dashboard.');
console.log('You can find your Supabase URL and anon key in your Supabase project settings > API.');
console.log('');

const envFile = '.env.local';
let supabaseUrl = '';
let supabaseKey = '';

rl.question('Enter your Supabase URL: ', (url) => {
  supabaseUrl = url.trim();
  
  rl.question('Enter your Supabase anon key: ', (key) => {
    supabaseKey = key.trim();
    
    // Create or update .env.local file
    const envContent = `# Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=${supabaseUrl}
NEXT_PUBLIC_SUPABASE_ANON_KEY=${supabaseKey}
`;
    
    fs.writeFileSync(envFile, envContent);
    
    console.log(`\nCredentials saved to ${envFile}`);
    console.log('You can now run "npm run dev" to start the development server.');
    
    rl.close();
  });
}); 