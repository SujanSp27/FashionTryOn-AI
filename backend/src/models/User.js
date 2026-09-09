/**
 * User Mongoose Model
 */

const mongoose = require('mongoose');

const userSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'User name is required'],
      trim: true
    },
    email: {
      type: String,
      required: [true, 'User email is required'],
      unique: true,
      lowercase: true,
      trim: true,
      match: [/^\S+@\S+\.\S+$/, 'Please provide a valid email address']
    },
    passwordHash: {
      type: String,
      required: [true, 'Password hash is required']
    },
    profileImage: {
      type: String,
      default: null
    }
  },
  {
    timestamps: true
  }
);

// Note: unique: true in email field definition automatically creates the unique index
module.exports = mongoose.model('User', userSchema);

