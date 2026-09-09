/**
 * Health Diagnostic Routes
 */

const express = require('express');
const router = express.Router();
const aiService = require('../services/ai.service');
const { isDatabaseConnected } = require('../config/database');

// GET /api/health - Local Backend & Database Liveness Check
router.get('/', (req, res) => {
  const dbStatus = isDatabaseConnected() ? 'connected' : 'disconnected';
  return res.status(200).json({
    status: 'ok',
    service: 'virtual-try-on-backend',
    database: {
      status: dbStatus
    }
  });
});

// GET /api/health/db - Dedicated Database Diagnostic Endpoint
router.get('/db', (req, res) => {
  const connected = isDatabaseConnected();
  if (connected) {
    return res.status(200).json({
      status: 'ok',
      database: 'mongodb',
      connection: 'connected'
    });
  } else {
    return res.status(503).json({
      status: 'error',
      database: 'mongodb',
      connection: 'disconnected'
    });
  }
});

// GET /api/health/ai - End-to-End AI Service Diagnostic
router.get('/ai', async (req, res) => {
  try {
    const aiHealth = await aiService.checkAiHealth();
    return res.status(200).json({
      status: 'ok',
      backend: 'healthy',
      aiService: aiHealth
    });
  } catch (err) {
    return res.status(err.status || 502).json({
      status: 'error',
      backend: 'healthy',
      aiService: {
        status: 'unavailable',
        error: err.code || 'AI_SERVICE_UNAVAILABLE',
        message: err.message
      }
    });
  }
});

module.exports = router;
