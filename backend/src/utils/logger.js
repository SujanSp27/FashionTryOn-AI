/**
 * Structured Application Logger
 */

const getTimestamp = () => new Date().toISOString();

const logger = {
  info: (msg, meta = {}) => {
    const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
    console.log(`[${getTimestamp()}] [INFO] ${msg}${metaStr}`);
  },
  warn: (msg, meta = {}) => {
    const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
    console.warn(`[${getTimestamp()}] [WARN] ${msg}${metaStr}`);
  },
  error: (msg, err = null) => {
    const errStr = err ? ` | Error: ${err.message || err}` : '';
    console.error(`[${getTimestamp()}] [ERROR] ${msg}${errStr}`);
    if (err && err.stack && process.env.NODE_ENV !== 'production') {
      console.error(err.stack);
    }
  },
  tryon: (requestId, msg) => {
    console.log(`[${getTimestamp()}] [TRYON] [${requestId}] ${msg}`);
  }
};

module.exports = logger;
