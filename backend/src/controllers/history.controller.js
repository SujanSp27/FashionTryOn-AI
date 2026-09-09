/**
 * Try-On History Controller
 * Handles CRUD and retrieval of virtual try-on activity records.
 */

const mongoose = require('mongoose');
const TryOnHistory = require('../models/TryOnHistory');
const logger = require('../utils/logger');

class HistoryController {
  // POST /api/history - Manually record a try-on history entry
  async createHistory(req, res, next) {
    try {
      const {
        user,
        garment,
        personImageUrl,
        garmentImageUrl,
        resultImageUrl,
        status = 'pending',
        processingTimeMs,
        errorMessage
      } = req.body;

      if (user && !mongoose.Types.ObjectId.isValid(user)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: 'Invalid user ObjectId.'
        });
      }

      if (garment && !mongoose.Types.ObjectId.isValid(garment)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: 'Invalid garment ObjectId.'
        });
      }

      const record = await TryOnHistory.create({
        user: user || null,
        garment: garment || null,
        personImageUrl: personImageUrl || null,
        garmentImageUrl: garmentImageUrl || null,
        resultImageUrl: resultImageUrl || null,
        status,
        processingTimeMs: processingTimeMs || null,
        errorMessage: errorMessage || null
      });

      return res.status(201).json({
        status: 'success',
        data: record
      });
    } catch (err) {
      next(err);
    }
  }

  // GET /api/history - List try-on history (sorted by createdAt DESC)
  async listHistory(req, res, next) {
    try {
      const { user, status, limit = 50, skip = 0 } = req.query;
      const query = {};

      if (user) {
        if (!mongoose.Types.ObjectId.isValid(user)) {
          return res.status(400).json({
            error: 'INVALID_ID',
            message: 'Invalid user ObjectId.'
          });
        }
        query.user = user;
      }

      if (status) {
        query.status = status.trim().toLowerCase();
      }

      const total = await TryOnHistory.countDocuments(query);
      const history = await TryOnHistory.find(query)
        .populate('garment', 'name category imageUrl')
        .sort({ createdAt: -1 })
        .skip(parseInt(skip, 10) || 0)
        .limit(Math.min(parseInt(limit, 10) || 50, 100));

      return res.status(200).json({
        status: 'success',
        total,
        count: history.length,
        data: history
      });
    } catch (err) {
      next(err);
    }
  }

  // GET /api/history/:id - Get a specific history entry
  async getHistoryById(req, res, next) {
    try {
      const { id } = req.params;
      if (!mongoose.Types.ObjectId.isValid(id)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: `Invalid history ID '${id}'.`
        });
      }

      const record = await TryOnHistory.findById(id)
        .populate('garment', 'name category imageUrl');

      if (!record) {
        return res.status(404).json({
          error: 'NOT_FOUND',
          message: `Try-on history record '${id}' not found.`
        });
      }

      return res.status(200).json({
        status: 'success',
        data: record
      });
    } catch (err) {
      next(err);
    }
  }

  // DELETE /api/history/:id - Delete a history entry
  async deleteHistory(req, res, next) {
    try {
      const { id } = req.params;
      if (!mongoose.Types.ObjectId.isValid(id)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: `Invalid history ID '${id}'.`
        });
      }

      const deleted = await TryOnHistory.findByIdAndDelete(id);
      if (!deleted) {
        return res.status(404).json({
          error: 'NOT_FOUND',
          message: `Try-on history record '${id}' not found.`
        });
      }

      return res.status(200).json({
        status: 'success',
        message: 'History record deleted successfully.'
      });
    } catch (err) {
      next(err);
    }
  }
}

module.exports = new HistoryController();
