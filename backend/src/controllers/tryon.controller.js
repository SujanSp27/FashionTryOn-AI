/**
 * Try-On Controller
 * Validates uploads, coordinates AI service invocation, and records try-on history.
 */

const mongoose = require('mongoose');
const aiService = require('../services/ai.service');
const { validateImageMagicBytes } = require('../middleware/upload.middleware');
const { isDatabaseConnected } = require('../config/database');
const TryOnHistory = require('../models/TryOnHistory');
const logger = require('../utils/logger');

const ALLOWED_BG_MODES = new Set(['ai', 'simple', 'provided_mask']);

class TryonController {
  async handleTryOn(req, res, next) {
    const reqId = req.id || 'unknown';
    const tStart = Date.now();
    let historyRecord = null;

    try {
      logger.tryon(reqId, 'Request received');

      // 1. Validate required files exist
      if (!req.files || !req.files['person'] || !req.files['person'][0]) {
        return res.status(400).json({
          error: 'MISSING_FILE',
          message: "The 'person' image file is required in multipart form-data."
        });
      }

      if (!req.files || !req.files['garment'] || !req.files['garment'][0]) {
        return res.status(400).json({
          error: 'MISSING_FILE',
          message: "The 'garment' image file is required in multipart form-data."
        });
      }

      const personFile = req.files['person'][0];
      const garmentFile = req.files['garment'][0];

      // 2. Validate bg_mode parameter
      const rawBgMode = (req.body.bg_mode || 'ai').trim().toLowerCase();
      if (!ALLOWED_BG_MODES.has(rawBgMode)) {
        return res.status(400).json({
          error: 'INVALID_PARAMETER',
          message: `Invalid 'bg_mode': '${req.body.bg_mode}'. Allowed values: 'ai', 'simple', 'provided_mask'.`
        });
      }

      // 3. Inspect binary magic bytes
      validateImageMagicBytes(personFile.buffer, 'person image');
      validateImageMagicBytes(garmentFile.buffer, 'garment image');

      // 4. Log upload sizes
      const personSizeMB = (personFile.size / (1024 * 1024)).toFixed(2);
      const garmentSizeMB = (garmentFile.size / (1024 * 1024)).toFixed(2);
      logger.tryon(reqId, `Person: ${personSizeMB} MB (${personFile.mimetype}), Garment: ${garmentSizeMB} MB (${garmentFile.mimetype})`);

      // 5. Optional History Tracking in MongoDB (status='processing')
      const userId = req.body.user && mongoose.Types.ObjectId.isValid(req.body.user) ? req.body.user : null;
      const garmentId = req.body.garment && mongoose.Types.ObjectId.isValid(req.body.garment) ? req.body.garment : null;

      if (isDatabaseConnected()) {
        try {
          historyRecord = await TryOnHistory.create({
            user: userId,
            garment: garmentId,
            personImageUrl: null,
            garmentImageUrl: null,
            resultImageUrl: null,
            status: 'processing'
          });
        } catch (dbErr) {
          logger.warn(`[TRYON] [${reqId}] Could not create initial TryOnHistory document: ${dbErr.message}`);
        }
      }

      // 6. Dispatch to AI Service
      logger.tryon(reqId, 'Calling AI service...');
      let result;
      try {
        result = await aiService.generateTryOn({
          personBuffer: personFile.buffer,
          personMimeType: personFile.mimetype,
          personFilename: personFile.originalname,
          garmentBuffer: garmentFile.buffer,
          garmentMimeType: garmentFile.mimetype,
          garmentFilename: garmentFile.originalname,
          bgMode: rawBgMode,
          requestId: reqId
        });
      } catch (aiErr) {
        // Update history status='failed' if AI inference fails
        if (historyRecord) {
          try {
            await TryOnHistory.findByIdAndUpdate(historyRecord._id, {
              status: 'failed',
              errorMessage: aiErr.message || 'AI inference error',
              processingTimeMs: Date.now() - tStart
            });
          } catch (updateErr) {
            logger.warn(`[TRYON] [${reqId}] Failed to update failed history record: ${updateErr.message}`);
          }
        }
        throw aiErr;
      }

      const totalElapsedSec = ((Date.now() - tStart) / 1000).toFixed(3);
      const totalElapsedMs = Date.now() - tStart;
      logger.tryon(reqId, `Completed in ${totalElapsedSec}s (AI Roundtrip: ${result.timings.roundTripSec}s)`);

      // 7. Update history status='completed'
      if (historyRecord) {
        try {
          await TryOnHistory.findByIdAndUpdate(historyRecord._id, {
            status: 'completed',
            processingTimeMs: totalElapsedMs
          });
        } catch (dbErr) {
          logger.warn(`[TRYON] [${reqId}] Could not update completed TryOnHistory document: ${dbErr.message}`);
        }
      }

      // 8. Return raw binary JPEG image directly to client
      res.setHeader('Content-Type', result.contentType);
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
      res.setHeader('X-Gateway-Elapsed-Sec', totalElapsedSec);
      if (historyRecord) {
        res.setHeader('X-History-ID', historyRecord._id.toString());
      }
      if (result.timings.aiTotalSec) {
        res.setHeader('X-AI-Process-Time-Total', result.timings.aiTotalSec);
      }
      if (result.timings.aiGarmentSec) {
        res.setHeader('X-AI-Process-Time-Garment', result.timings.aiGarmentSec);
      }
      if (result.timings.aiVtonSec) {
        res.setHeader('X-AI-Process-Time-VTON', result.timings.aiVtonSec);
      }

      return res.status(200).send(result.imageBuffer);
    } catch (err) {
      next(err);
    }
  }
}

module.exports = new TryonController();
