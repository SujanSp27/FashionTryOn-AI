/**
 * Garment Routes
 */

const express = require('express');
const router = express.Router();
const garmentController = require('../controllers/garment.controller');

router.post('/', garmentController.createGarment);
router.get('/', garmentController.listGarments);
router.get('/:id', garmentController.getGarmentById);
router.put('/:id', garmentController.updateGarment);
router.delete('/:id', garmentController.deleteGarment);

module.exports = router;
