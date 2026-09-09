/**
 * Request ID Middleware
 * Assigns a unique X-Request-ID to every incoming request.
 */

const crypto = require('crypto');

function requestIdMiddleware(req, res, next) {
  const existingId = req.headers['x-request-id'];
  const reqId = existingId && typeof existingId === 'string' 
    ? existingId 
    : (crypto.randomUUID ? crypto.randomUUID().slice(0, 8) : Math.random().toString(36).substring(2, 10));

  req.id = reqId;
  res.setHeader('X-Request-ID', reqId);
  next();
}

module.exports = requestIdMiddleware;
