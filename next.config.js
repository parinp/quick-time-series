/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Configure transpilation for plotly.js
  transpilePackages: ['plotly.js', 'react-plotly.js'],
};

module.exports = nextConfig; 