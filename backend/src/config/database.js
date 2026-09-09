/**
 * Database Connection Module
 * Connects to MongoDB Atlas using Mongoose.
 * Sanitizes logs to ensure no credentials or URIs are ever exposed.
 */

const mongoose = require('mongoose');
const config = require('./env');
const logger = require('../utils/logger');

let isConnected = false;

async function connectDatabase() {
  if (isConnected && mongoose.connection.readyState === 1) {
    return mongoose.connection;
  }

  try {
    const conn = await mongoose.connect(config.mongodbUri, {
      serverSelectionTimeoutMS: 10000,
      maxPoolSize: 10
    });

    isConnected = true;
    const dbName = conn.connection.name || 'default';
    const host = conn.connection.host || 'unknown';

    // Log connection success safely: NEVER log credentials, password, or full URI
    logger.info(`[DATABASE] MongoDB connection successful`);
    logger.info(`[DATABASE] Database name: ${dbName}`);
    logger.info(`[DATABASE] Connection state: connected (host: ${host})`);

    mongoose.connection.on('error', (err) => {
      logger.error(`[DATABASE] MongoDB runtime error: ${err.message}`);
    });

    mongoose.connection.on('disconnected', () => {
      isConnected = false;
      logger.warn('[DATABASE] MongoDB disconnected');
    });

    mongoose.connection.on('reconnected', () => {
      isConnected = true;
      logger.info('[DATABASE] MongoDB reconnected');
    });

    return conn;
  } catch (err) {
    isConnected = false;
    logger.error(`[DATABASE] MongoDB connection failure: ${err.message}`);
    throw err;
  }
}

function isDatabaseConnected() {
  return mongoose.connection.readyState === 1;
}

async function disconnectDatabase() {
  if (mongoose.connection.readyState !== 0) {
    await mongoose.disconnect();
    isConnected = false;
    logger.info('[DATABASE] MongoDB disconnected cleanly');
  }
}

module.exports = {
  connectDatabase,
  isDatabaseConnected,
  disconnectDatabase
};
