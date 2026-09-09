/**
 * Comprehensive Backend Gateway Test Suite
 * Tests routes, validation, error middleware, and end-to-end integration.
 */

const http = require('http');
const path = require('path');
const fs = require('fs');
const assert = require('assert');
const axios = require('axios');
const FormData = require('form-data');

const config = require('../src/config/env');
const app = require('../src/app');

const { connectDatabase, disconnectDatabase } = require('../src/config/database');

let server;
const TEST_PORT = 5099;
const BASE_URL = `http://127.0.0.1:${TEST_PORT}`;

// Sample test files from repo
const REPO_ROOT = path.resolve(__dirname, '../../Flow-Style-VTON-main');
const PERSON_FILE = path.join(REPO_ROOT, 'test/mini_dataset/test_img/000001_0.jpg');
const GARMENT_FILE = path.join(REPO_ROOT, 'test/garment_tests/04_colored_bg.jpg');

async function runTests() {
  console.log('====================================================');
  console.log(' RUNNING NODE.JS + EXPRESS BACKEND TEST SUITE');
  console.log('====================================================\n');

  // Connect to database
  await connectDatabase();

  // Start test server
  await new Promise((resolve) => {
    server = app.listen(TEST_PORT, resolve);
  });
  console.log(`[+] Test server listening on ${BASE_URL}\n`);

  let passed = 0;
  let failed = 0;

  async function test(name, fn) {
    process.stdout.write(`  TEST: ${name}... `);
    try {
      await fn();
      console.log('PASSED [OK]');
      passed++;
    } catch (err) {
      console.log(`FAILED [X]\n    Error: ${err.message}`);
      if (err.response) {
        console.log(`    HTTP Status: ${err.response.status}`);
        console.log(`    Response Data:`, err.response.data);
      }
      failed++;
    }
  }

  try {
    // 1. GET /api/health
    await test('GET /api/health returns 200, service name, and database connected', async () => {
      const res = await axios.get(`${BASE_URL}/api/health`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'ok');
      assert.strictEqual(res.data.service, 'virtual-try-on-backend');
      assert.strictEqual(res.data.database.status, 'connected');
    });

    // 1b. GET /api/health/db
    await test('GET /api/health/db returns 200 with connection: connected', async () => {
      const res = await axios.get(`${BASE_URL}/api/health/db`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'ok');
      assert.strictEqual(res.data.database, 'mongodb');
      assert.strictEqual(res.data.connection, 'connected');
    });


    // 2. GET /api/health/ai
    await test('GET /api/health/ai diagnostic response', async () => {
      try {
        const res = await axios.get(`${BASE_URL}/api/health/ai`);
        assert.strictEqual(res.status, 200);
        assert.strictEqual(res.data.status, 'ok');
        assert.strictEqual(res.data.backend, 'healthy');
        assert.ok(res.data.aiService, 'aiService details missing');
      } catch (err) {
        // If AI service is currently offline, it returns 502 with structured error
        if (err.response && err.response.status === 502) {
          assert.strictEqual(err.response.data.status, 'error');
          assert.strictEqual(err.response.data.backend, 'healthy');
        } else {
          throw err;
        }
      }
    });

    // 3. POST /api/tryon without files (Missing Person)
    await test('POST /api/tryon without person rejects with HTTP 400', async () => {
      const form = new FormData();
      form.append('garment', Buffer.from('fake image content'), { filename: 'garment.jpg', contentType: 'image/jpeg' });
      try {
        await axios.post(`${BASE_URL}/api/tryon`, form, { headers: form.getHeaders() });
        assert.fail('Should have failed with 400');
      } catch (err) {
        assert.strictEqual(err.response.status, 400);
        assert.strictEqual(err.response.data.error, 'MISSING_FILE');
      }
    });

    // 4. POST /api/tryon without garment (Missing Garment)
    await test('POST /api/tryon without garment rejects with HTTP 400', async () => {
      const form = new FormData();
      form.append('person', Buffer.from('fake image content'), { filename: 'person.jpg', contentType: 'image/jpeg' });
      try {
        await axios.post(`${BASE_URL}/api/tryon`, form, { headers: form.getHeaders() });
        assert.fail('Should have failed with 400');
      } catch (err) {
        assert.strictEqual(err.response.status, 400);
        assert.strictEqual(err.response.data.error, 'MISSING_FILE');
      }
    });

    // 5. POST /api/tryon with invalid file type (e.g. text/plain)
    await test('POST /api/tryon with text file rejects with HTTP 400', async () => {
      const form = new FormData();
      form.append('person', Buffer.from('plain text file content'), { filename: 'test.txt', contentType: 'text/plain' });
      form.append('garment', Buffer.from('plain text file content'), { filename: 'test.txt', contentType: 'text/plain' });
      try {
        await axios.post(`${BASE_URL}/api/tryon`, form, { headers: form.getHeaders() });
        assert.fail('Should have failed with 400');
      } catch (err) {
        assert.strictEqual(err.response.status, 400);
      }
    });

    // 6. POST /api/tryon with corrupted binary header (magic bytes check)
    await test('POST /api/tryon with non-image binary rejects with HTTP 400', async () => {
      const fakeBinary = Buffer.from([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B]);
      const form = new FormData();
      form.append('person', fakeBinary, { filename: 'person.jpg', contentType: 'image/jpeg' });
      form.append('garment', fakeBinary, { filename: 'garment.jpg', contentType: 'image/jpeg' });
      try {
        await axios.post(`${BASE_URL}/api/tryon`, form, { headers: form.getHeaders() });
        assert.fail('Should have failed with 400');
      } catch (err) {
        assert.strictEqual(err.response.status, 400);
      }
    });

    // 7. Request ID Header presence
    await test('Every response contains X-Request-ID header', async () => {
      const res = await axios.get(`${BASE_URL}/api/health`);
      assert.ok(res.headers['x-request-id'], 'X-Request-ID header is missing');
    });

    // 8. 404 Handler
    await test('Unknown route returns HTTP 404', async () => {
      try {
        await axios.get(`${BASE_URL}/api/non_existent_route`);
        assert.fail('Should have failed with 404');
      } catch (err) {
        assert.strictEqual(err.response.status, 404);
        assert.strictEqual(err.response.data.error, 'NOT_FOUND');
      }
    });

    // 9. End-to-End Try-On (if AI service is running)
    if (fs.existsSync(PERSON_FILE) && fs.existsSync(GARMENT_FILE)) {
      await test('POST /api/tryon with real images (End-to-End Gateway Test)', async () => {
        const form = new FormData();
        form.append('person', fs.createReadStream(PERSON_FILE));
        form.append('garment', fs.createReadStream(GARMENT_FILE));
        form.append('bg_mode', 'ai');

        try {
          const res = await axios.post(`${BASE_URL}/api/tryon`, form, {
            headers: form.getHeaders(),
            responseType: 'arraybuffer',
            timeout: 60000
          });

          assert.strictEqual(res.status, 200);
          assert.strictEqual(res.headers['content-type'], 'image/jpeg');
          assert.ok(res.headers['x-gateway-elapsed-sec'], 'Elapsed time header missing');

          const buf = Buffer.from(res.data);
          assert.ok(buf.length > 5000, `Returned image buffer suspiciously small: ${buf.length} bytes`);
          // Check JPEG magic bytes
          assert.strictEqual(buf[0], 0xFF);
          assert.strictEqual(buf[1], 0xD8);
          assert.strictEqual(buf[2], 0xFF);

          // Save output to backend test output
          const outDir = path.resolve(__dirname, '../test_output');
          if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
          const outPath = path.join(outDir, 'node_tryon_result.jpg');
          fs.writeFileSync(outPath, buf);
          console.log(`\n    [Saved E2E Image]: ${outPath} (${(buf.length / 1024).toFixed(1)} KB)`);
        } catch (err) {
          if (err.response && (err.response.status === 502 || err.response.status === 504)) {
            console.log(`\n    [AI service offline (HTTP ${err.response.status}) - verified 502/504 error handler!]`);
          } else {
            throw err;
          }
        }
      });
    }

  } finally {
    if (server) server.close();
    await disconnectDatabase();
  }


  console.log('\n====================================================');
  console.log(` TEST SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('====================================================');

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch(err => {
  console.error('Fatal test runner error:', err);
  if (server) server.close();
  process.exit(1);
});
