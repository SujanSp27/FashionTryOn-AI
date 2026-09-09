/**
 * Try-On History Routes
 */

const express = require('express');
const router = express.Router();
const historyController = require('../controllers/history.controller');

router.post('/', historyController.createHistory);
router.get('/', historyController.listHistory);
router.get('/:id', historyController.getHistoryById);
router.delete('/:id', historyController.deleteHistory);

module.exports = router;
