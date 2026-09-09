/**
 * AI Service Communication Layer
 * Handles HTTP requests to the Flow-Style-VTON FastAPI service.
 */

const axios = require('axios');
const FormData = require('form-data');
const config = require('../config/env');
const logger = require('../utils/logger');

class AiService {
  /**
   * Health check on the downstream FastAPI AI service.
   * Calls GET ${AI_SERVICE_URL}/health
   */
  async checkAiHealth() {
    try {
      const response = await axios.get(`${config.aiServiceUrl}/health`, {
        headers: {
          'ngrok-skip-browser-warning': '1',
          'User-Agent': 'FitFusionBackend/1.0'
        },
        timeout: 5000 // 5s timeout for health check
      });
      return response.data;
    } catch (err) {
      logger.error(`AI Health check failed against ${config.aiServiceUrl}/health`, err);
      if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
        const error = new Error(`AI service is unreachable at ${config.aiServiceUrl}`);
        error.code = 'AI_UNREACHABLE';
        error.status = 502;
        throw error;
      }
      if (err.code === 'ECONNABORTED') {
        const error = new Error('AI health check timed out');
        error.code = 'AI_TIMEOUT';
        error.status = 504;
        throw error;
      }
      const error = new Error('AI service reported an error during health check');
      error.code = 'AI_ERROR';
      error.status = err.response ? err.response.status : 502;
      error.details = err.response ? err.response.data : err.message;
      throw error;
    }
  }

  /**
   * Dispatches a single-pair try-on request to FastAPI.
   * Calls POST ${AI_SERVICE_URL}/tryon as multipart/form-data.
   * Returns raw binary Buffer (JPEG image).
   */
  async generateTryOn({
    personBuffer,
    personMimeType = 'image/jpeg',
    personFilename = 'person.jpg',
    garmentBuffer,
    garmentMimeType = 'image/jpeg',
    garmentFilename = 'garment.jpg',
    bgMode = 'ai',
    requestId = 'unknown'
  }) {
    const t0 = Date.now();
    logger.tryon(requestId, `Dispatching request to AI service: ${config.aiServiceUrl}/tryon (bg_mode='${bgMode}')`);

    const form = new FormData();
    form.append('person', personBuffer, {
      filename: personFilename,
      contentType: personMimeType
    });
    form.append('garment', garmentBuffer, {
      filename: garmentFilename,
      contentType: garmentMimeType
    });
    form.append('bg_mode', bgMode);

    try {
      const response = await axios.post(`${config.aiServiceUrl}/tryon`, form, {
        headers: {
          ...form.getHeaders(),
          'X-Request-ID': requestId,
          'ngrok-skip-browser-warning': '1',
          'User-Agent': 'FitFusionBackend/1.0'
        },
        responseType: 'arraybuffer', // Receive binary buffer directly
        timeout: config.aiRequestTimeout,
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      });

      const durationSec = ((Date.now() - t0) / 1000).toFixed(3);
      logger.tryon(requestId, `AI service responded with HTTP ${response.status} in ${durationSec}s`);

      const totalTimeHeader = response.headers['x-process-time-total'];
      const vtonTimeHeader = response.headers['x-process-time-vton'];
      const garmentTimeHeader = response.headers['x-process-time-garment'];

      return {
        imageBuffer: Buffer.from(response.data),
        contentType: response.headers['content-type'] || 'image/jpeg',
        timings: {
          roundTripSec: durationSec,
          aiTotalSec: totalTimeHeader || null,
          aiVtonSec: vtonTimeHeader || null,
          aiGarmentSec: garmentTimeHeader || null
        }
      };
    } catch (err) {
      const durationSec = ((Date.now() - t0) / 1000).toFixed(3);
      logger.error(`[TRYON] [${requestId}] AI request failed after ${durationSec}s: ${err.message}`);

      // Handle timeout
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        const error = new Error('The virtual try-on AI service took too long to respond. Please try again.');
        error.code = 'AI_SERVICE_TIMEOUT';
        error.status = 504;
        throw error;
      }

      // Handle connection refused / offline
      if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
        const error = new Error('The virtual try-on AI service is currently unreachable. Ensure Google Colab / FastAPI is running.');
        error.code = 'AI_SERVICE_UNAVAILABLE';
        error.status = 502;
        throw error;
      }

      // Handle response errors from FastAPI (400, 500, 503)
      if (err.response) {
        let serverErrorDetail = 'AI inference error';
        try {
          if (Buffer.isBuffer(err.response.data)) {
            const parsed = JSON.parse(err.response.data.toString('utf-8'));
            serverErrorDetail = parsed.detail || parsed.error || serverErrorDetail;
          }
        } catch {
          // If not json, use statusText
          serverErrorDetail = err.response.statusText || serverErrorDetail;
        }

        const error = new Error(typeof serverErrorDetail === 'object' ? JSON.stringify(serverErrorDetail) : serverErrorDetail);
        error.code = err.response.status === 400 ? 'INVALID_INPUT' : 'AI_INFERENCE_FAILED';
        error.status = err.response.status;
        error.details = serverErrorDetail;
        throw error;
      }

      const error = new Error('Unexpected error communicating with virtual try-on service.');
      error.code = 'INTERNAL_GATEWAY_ERROR';
      error.status = 500;
      throw error;
    }
  }
}

module.exports = new AiService();
