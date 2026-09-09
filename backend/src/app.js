/**
 * Express Application Configuration
 */

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const morgan = require('morgan');
const config = require('./config/env');
const requestIdMiddleware = require('./middleware/request-id.middleware');
const { notFoundHandler, errorHandler } = require('./middleware/error.middleware');

const healthRoutes = require('./routes/health.routes');
const tryonRoutes = require('./routes/tryon.routes');
const garmentRoutes = require('./routes/garment.routes');
const historyRoutes = require('./routes/history.routes');

const app = express();

// Security Headers
app.use(helmet());

// CORS Configuration
const allowedOrigins = config.corsOrigin.split(',').map(o => o.trim());
app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (e.g. mobile apps, curl) or matched origin
    if (!origin || allowedOrigins.includes(origin) || allowedOrigins.includes('*')) {
      return callback(null, true);
    }
    return callback(new Error(`Origin '${origin}' not allowed by CORS policy.`));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID']
}));

// Request ID
app.use(requestIdMiddleware);

// HTTP Access Logging
morgan.token('id', (req) => req.id || '-');
if (config.nodeEnv !== 'test') {
  app.use(morgan('[:date[iso]] [HTTP] [:id] :method :url :status :res[content-length] - :response-time ms'));
}

// Body parsing for JSON payloads (Try-On uses multer for multipart/form-data)
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// Route Mounts
app.use('/api/health', healthRoutes);
app.use('/api/tryon', tryonRoutes);
app.use('/api/garments', garmentRoutes);
app.use('/api/history', historyRoutes);

// Error Handling
app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
