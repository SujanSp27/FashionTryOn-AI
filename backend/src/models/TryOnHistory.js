/**
 * TryOnHistory Mongoose Model
 */

const mongoose = require('mongoose');

const tryOnHistorySchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      default: null
    },
    garment: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Garment',
      default: null
    },
    personImageUrl: {
      type: String,
      default: null
    },
    garmentImageUrl: {
      type: String,
      default: null
    },
    resultImageUrl: {
      type: String,
      default: null
    },
    status: {
      type: String,
      enum: {
        values: ['pending', 'processing', 'completed', 'failed'],
        message: '{VALUE} is not a valid try-on status'
      },
      default: 'pending'
    },
    processingTimeMs: {
      type: Number,
      default: null
    },
    errorMessage: {
      type: String,
      default: null
    }
  },
  {
    timestamps: true
  }
);

tryOnHistorySchema.index({ user: 1 });
tryOnHistorySchema.index({ createdAt: -1 });
tryOnHistorySchema.index({ status: 1 });

module.exports = mongoose.model('TryOnHistory', tryOnHistorySchema);
