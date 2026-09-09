/**
 * Server Entry Point
 * Ensures MongoDB Atlas connects first, then starts Express server.
 */

const app = require('./app');
const config = require('./config/env');
const { connectDatabase, disconnectDatabase } = require('./config/database');
const logger = require('./utils/logger');
const aiService = require('./services/ai.service');

let server;

async function startServer() {
  try {
    // 1. Connect to MongoDB Atlas first
    logger.info('Connecting to MongoDB Atlas...');
    await connectDatabase();

    // 2. Start Express HTTP Server
    server = app.listen(config.port, async () => {
      logger.info('====================================================');
      logger.info(` Virtual Try-On Backend Gateway Online`);
      logger.info(` Port:              ${config.port}`);
      logger.info(` Environment:       ${config.nodeEnv}`);
      logger.info(` Database:          Connected to MongoDB Atlas`);
      logger.info(` AI Service Target: ${config.aiServiceUrl}`);
      logger.info(` CORS Allowed:      ${config.corsOrigin}`);
      logger.info(` Max Upload:        ${config.maxFileSizeMB} MB`);
      logger.info('====================================================');

      // Check downstream AI service connectivity
      try {
        const aiHealth = await aiService.checkAiHealth();
        logger.info(`[+] Connected to AI Service: ${aiHealth.service} (${aiHealth.model}, ${aiHealth.device})`);
      } catch (err) {
        logger.warn(`[-] Downstream AI service is unreachable at ${config.aiServiceUrl} (${err.message})`);
      }
    });

  } catch (err) {
    logger.error(`[FATAL] Startup aborted due to database connection error: ${err.message}`);
    process.exit(1);
  }
}

// Graceful Shutdown
async function handleShutdown(signal) {
  logger.info(`Received ${signal}. Shutting down gracefully...`);
  if (server) {
    server.close(async () => {
      logger.info('HTTP server closed.');
      await disconnectDatabase();
      process.exit(0);
    });
  } else {
    await disconnectDatabase();
    process.exit(0);
  }
}

process.on('SIGTERM', () => handleShutdown('SIGTERM'));
process.on('SIGINT', () => handleShutdown('SIGINT'));

startServer();

module.exports = server;
