/**
 * Garment Controller
 * Handles CRUD operations for catalog & user garments.
 */

const mongoose = require('mongoose');
const Garment = require('../models/Garment');
const logger = require('../utils/logger');

class GarmentController {
  // POST /api/garments - Create a new garment
  async createGarment(req, res, next) {
    try {
      const { name, description, category, imageUrl, thumbnailUrl, createdBy } = req.body;

      if (!name || typeof name !== 'string' || !name.trim()) {
        return res.status(400).json({
          error: 'VALIDATION_ERROR',
          message: 'Garment name is required.'
        });
      }

      if (createdBy && !mongoose.Types.ObjectId.isValid(createdBy)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: 'Invalid createdBy user ObjectId.'
        });
      }

      const garment = await Garment.create({
        name: name.trim(),
        description: (description || '').trim(),
        category: (category || 'other').trim().toLowerCase(),
        imageUrl: imageUrl || null,
        thumbnailUrl: thumbnailUrl || null,
        createdBy: createdBy || null
      });

      return res.status(201).json({
        status: 'success',
        data: garment
      });
    } catch (err) {
      next(err);
    }
  }

  // GET /api/garments - List garments with optional filtering & pagination
  async listGarments(req, res, next) {
    try {
      const { category, createdBy, limit = 50, skip = 0 } = req.query;
      const query = {};

      if (category) {
        query.category = category.trim().toLowerCase();
      }

      if (createdBy) {
        if (!mongoose.Types.ObjectId.isValid(createdBy)) {
          return res.status(400).json({
            error: 'INVALID_ID',
            message: 'Invalid createdBy user ObjectId.'
          });
        }
        query.createdBy = createdBy;
      }

      const total = await Garment.countDocuments(query);
      const garments = await Garment.find(query)
        .sort({ createdAt: -1 })
        .skip(parseInt(skip, 10) || 0)
        .limit(Math.min(parseInt(limit, 10) || 50, 100));

      return res.status(200).json({
        status: 'success',
        total,
        count: garments.length,
        data: garments
      });
    } catch (err) {
      next(err);
    }
  }

  // GET /api/garments/:id - Get a single garment by ID
  async getGarmentById(req, res, next) {
    try {
      const { id } = req.params;
      if (!mongoose.Types.ObjectId.isValid(id)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: `Invalid garment ID '${id}'.`
        });
      }

      const garment = await Garment.findById(id);
      if (!garment) {
        return res.status(404).json({
          error: 'NOT_FOUND',
          message: `Garment with ID '${id}' not found.`
        });
      }

      return res.status(200).json({
        status: 'success',
        data: garment
      });
    } catch (err) {
      next(err);
    }
  }

  // PUT /api/garments/:id - Update a garment
  async updateGarment(req, res, next) {
    try {
      const { id } = req.params;
      if (!mongoose.Types.ObjectId.isValid(id)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: `Invalid garment ID '${id}'.`
        });
      }

      const updates = {};
      const allowedFields = ['name', 'description', 'category', 'imageUrl', 'thumbnailUrl'];
      for (const field of allowedFields) {
        if (req.body[field] !== undefined) {
          updates[field] = typeof req.body[field] === 'string' ? req.body[field].trim() : req.body[field];
        }
      }

      if (updates.name !== undefined && !updates.name) {
        return res.status(400).json({
          error: 'VALIDATION_ERROR',
          message: 'Garment name cannot be empty.'
        });
      }

      const updated = await Garment.findByIdAndUpdate(id, updates, {
        returnDocument: 'after',
        runValidators: true
      });


      if (!updated) {
        return res.status(404).json({
          error: 'NOT_FOUND',
          message: `Garment with ID '${id}' not found.`
        });
      }

      return res.status(200).json({
        status: 'success',
        data: updated
      });
    } catch (err) {
      next(err);
    }
  }

  // DELETE /api/garments/:id - Delete a garment
  async deleteGarment(req, res, next) {
    try {
      const { id } = req.params;
      if (!mongoose.Types.ObjectId.isValid(id)) {
        return res.status(400).json({
          error: 'INVALID_ID',
          message: `Invalid garment ID '${id}'.`
        });
      }

      const deleted = await Garment.findByIdAndDelete(id);
      if (!deleted) {
        return res.status(404).json({
          error: 'NOT_FOUND',
          message: `Garment with ID '${id}' not found.`
        });
      }

      return res.status(200).json({
        status: 'success',
        message: 'Garment deleted successfully.'
      });
    } catch (err) {
      next(err);
    }
  }
}

module.exports = new GarmentController();
