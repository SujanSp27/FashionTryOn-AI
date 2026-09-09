/**
 * Environment Configuration Module
 * Loads and validates environment variables.
 */

const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const port = parseInt(process.env.PORT || '5000', 10);
const nodeEnv = process.env.NODE_ENV || 'development';
const aiServiceUrl = (process.env.AI_SERVICE_URL || '').trim().replace(/\/+$/, '');
const corsOrigin = process.env.CORS_ORIGIN || 'http://localhost:5173';
const aiRequestTimeout = parseInt(process.env.AI_REQUEST_TIMEOUT_MS || '120000', 10);
const maxFileSizeMB = parseInt(process.env.MAX_FILE_SIZE_MB || '10', 10);
const mongodbUri = (process.env.MONGODB_URI || '').trim();

// Validate required configurations
if (!aiServiceUrl) {
  console.error('\n[CONFIG ERROR] AI_SERVICE_URL is required but not defined in environment.');
  console.error('Please set AI_SERVICE_URL in your .env file (e.g. AI_SERVICE_URL=http://127.0.0.1:8000)\n');
  process.exit(1);
}

if (!mongodbUri) {
  console.error('\n[CONFIG ERROR] MONGODB_URI is required but not defined in environment.');
  console.error('Please set MONGODB_URI in your .env file\n');
  process.exit(1);
}

const config = Object.freeze({
  port,
  nodeEnv,
  aiServiceUrl,
  corsOrigin,
  aiRequestTimeout,
  maxFileSizeMB,
  mongodbUri,
  isProd: nodeEnv === 'production',
  isDev: nodeEnv === 'development'
});

module.exports = config;
