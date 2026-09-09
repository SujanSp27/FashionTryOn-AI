/**
 * Multer Upload Middleware with Magic Bytes Inspection
 * Validates file sizes, allowed MIME types, and authentic image signatures in memory.
 */

const multer = require('multer');
const config = require('../config/env');

// Allowed image MIME types
const ALLOWED_MIME_TYPES = new Set([
  'image/jpeg',
  'image/jpg',
  'image/png',
  'image/webp',
  'image/bmp'
]);

// Memory storage: Keep images in RAM, do NOT save permanently to disk
const storage = multer.memoryStorage();

// Multer file filter
const fileFilter = (req, file, cb) => {
  const mime = (file.mimetype || '').toLowerCase();
  if (!ALLOWED_MIME_TYPES.has(mime)) {
    const err = new Error(`Unsupported file type '${mime}' for field '${file.fieldname}'. Allowed: JPG, PNG, WEBP, BMP.`);
    err.code = 'INVALID_FILE_TYPE';
    err.status = 400;
    return cb(err, false);
  }
  cb(null, true);
};

const upload = multer({
  storage,
  limits: {
    fileSize: config.maxFileSizeMB * 1024 * 1024, // e.g. 10MB limit
    files: 2
  },
  fileFilter
});

/**
 * Validates actual file signature (magic bytes) to prevent extension spoofing.
 */
function validateImageMagicBytes(buffer, fieldName = 'image') {
  if (!buffer || buffer.length < 12) {
    const err = new Error(`The uploaded ${fieldName} is empty or corrupted.`);
    err.status = 400;
    throw err;
  }

  // JPEG magic bytes: FF D8 FF
  const isJpeg = buffer[0] === 0xFF && buffer[1] === 0xD8 && buffer[2] === 0xFF;

  // PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
  const isPng = buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47;

  // WEBP magic bytes: RIFF .... WEBP
  const isWebp = buffer.toString('ascii', 0, 4) === 'RIFF' && buffer.toString('ascii', 8, 12) === 'WEBP';

  // BMP magic bytes: 42 4D (BM)
  const isBmp = buffer[0] === 0x42 && buffer[1] === 0x4D;

  if (!isJpeg && !isPng && !isWebp && !isBmp) {
    const err = new Error(`The uploaded ${fieldName} does not contain a valid JPEG, PNG, WEBP, or BMP binary header.`);
    err.status = 400;
    throw err;
  }

  return true;
}

module.exports = {
  upload,
  validateImageMagicBytes
};
