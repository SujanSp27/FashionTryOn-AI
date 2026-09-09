/**
 * Virtual Try-On Route Definition
 */

const express = require('express');
const router = express.Router();
const tryonController = require('../controllers/tryon.controller');
const { upload } = require('../middleware/upload.middleware');

// POST /api/tryon - Single-pair Virtual Try-On
router.post(
  '/',
  upload.fields([
    { name: 'person', maxCount: 1 },
    { name: 'garment', maxCount: 1 }
  ]),
  tryonController.handleTryOn
);

module.exports = router;
