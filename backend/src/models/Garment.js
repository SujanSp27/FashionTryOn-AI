/**
 * Garment Mongoose Model
 */

const mongoose = require('mongoose');

const garmentSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Garment name is required'],
      trim: true
    },
    description: {
      type: String,
      trim: true,
      default: ''
    },
    category: {
      type: String,
      trim: true,
      default: 'other'
    },
    imageUrl: {
      type: String,
      trim: true,
      default: null
    },
    thumbnailUrl: {
      type: String,
      trim: true,
      default: null
    },
    createdBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      default: null
    }
  },
  {
    timestamps: true
  }
);

garmentSchema.index({ createdBy: 1 });
garmentSchema.index({ category: 1 });
garmentSchema.index({ createdAt: -1 });

module.exports = mongoose.model('Garment', garmentSchema);
