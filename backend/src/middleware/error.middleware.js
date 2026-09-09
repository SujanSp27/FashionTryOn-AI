/**
 * Global Error Handling & 404 Middleware
 */

const multer = require('multer');
const logger = require('../utils/logger');

function notFoundHandler(req, res) {
  return res.status(404).json({
    error: 'NOT_FOUND',
    message: `Cannot ${req.method} ${req.originalUrl}`
  });
}

function errorHandler(err, req, res, next) {
  const reqId = req.id || 'unknown';

  // 1. Multer Size Limit Error
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      logger.warn(`[${reqId}] Uploaded file exceeded size limit`);
      return res.status(413).json({
        error: 'FILE_TOO_LARGE',
        message: 'The uploaded file exceeds the maximum allowed limit.'
      });
    }
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      logger.warn(`[${reqId}] Unexpected field: ${err.field}`);
      return res.status(400).json({
        error: 'UNEXPECTED_FIELD',
        message: `Unexpected file field '${err.field}'. Expected 'person' and 'garment'.`
      });
    }
  }

  // 2. Custom File Type Validation Error
  if (err.code === 'INVALID_FILE_TYPE') {
    return res.status(400).json({
      error: 'INVALID_FILE_TYPE',
      message: err.message
    });
  }

  // 3. Application Errors with specific status codes
  const status = err.status || 500;
  const errorName = err.code || (status === 400 ? 'BAD_REQUEST' : 'INTERNAL_ERROR');

  logger.error(`[${reqId}] Unhandled request error: ${err.message}`, err);

  return res.status(status).json({
    error: errorName,
    message: err.message || 'An unexpected error occurred processing your virtual try-on request.'
  });
}

module.exports = {
  notFoundHandler,
  errorHandler
};
