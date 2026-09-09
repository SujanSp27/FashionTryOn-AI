/**
 * Database & Model Test Suite
 * Tests MongoDB Atlas connection, Mongoose models, validation, and CRUD API endpoints.
 */

const assert = require('assert');
const mongoose = require('mongoose');
const axios = require('axios');

const app = require('../src/app');
const config = require('../src/config/env');
const { connectDatabase, isDatabaseConnected, disconnectDatabase } = require('../src/config/database');

const User = require('../src/models/User');
const Garment = require('../src/models/Garment');
const TryOnHistory = require('../src/models/TryOnHistory');

let server;
const TEST_PORT = 5098;
const BASE_URL = `http://127.0.0.1:${TEST_PORT}`;

// Track created test IDs for safe cleanup
const cleanup = {
  userIds: [],
  garmentIds: [],
  historyIds: []
};

async function runDatabaseTests() {
  console.log('====================================================');
  console.log(' RUNNING MONGODB ATLAS + MONGOOSE DATABASE TEST SUITE');
  console.log('====================================================\n');

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
    // 1. Database Connection Tests
    await test('Connects to MongoDB Atlas securely', async () => {
      assert.ok(config.mongodbUri, 'MONGODB_URI must be configured');
      const conn = await connectDatabase();
      assert.strictEqual(isDatabaseConnected(), true);
      assert.strictEqual(mongoose.connection.readyState, 1);
      assert.ok(conn.connection.name, 'Database name should be present');
    });

    // Start Express server for API tests
    await new Promise((resolve) => {
      server = app.listen(TEST_PORT, resolve);
    });

    // 2. Health Endpoints with Database Status
    await test('GET /api/health includes database status: connected', async () => {
      const res = await axios.get(`${BASE_URL}/api/health`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'ok');
      assert.strictEqual(res.data.database.status, 'connected');
    });

    await test('GET /api/health/db returns 200 with connection: connected', async () => {
      const res = await axios.get(`${BASE_URL}/api/health/db`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'ok');
      assert.strictEqual(res.data.database, 'mongodb');
      assert.strictEqual(res.data.connection, 'connected');
    });

    // 3. User Model Tests
    let createdUser;
    await test('User Model: creates valid user with timestamps and trimmed lowercase email', async () => {
      const uniqueEmail = `test_user_${Date.now()}@example.com`;
      createdUser = await User.create({
        name: ' Test User ',
        email: `  ${uniqueEmail.toUpperCase()}  `,
        passwordHash: '$2b$10$hashedPlaceholderForPrompt6Test'
      });

      cleanup.userIds.push(createdUser._id);
      assert.strictEqual(createdUser.name, 'Test User');
      assert.strictEqual(createdUser.email, uniqueEmail.toLowerCase());
      assert.ok(createdUser.createdAt instanceof Date);
      assert.ok(createdUser.updatedAt instanceof Date);
    });

    await test('User Model: enforces required fields (name, email, passwordHash)', async () => {
      try {
        await User.create({});
        assert.fail('Should fail validation');
      } catch (err) {
        assert.ok(err.errors.name, 'Expected name validation error');
        assert.ok(err.errors.email, 'Expected email validation error');
        assert.ok(err.errors.passwordHash, 'Expected passwordHash validation error');
      }
    });

    await test('User Model: enforces unique email constraint', async () => {
      try {
        await User.create({
          name: 'Duplicate User',
          email: createdUser.email,
          passwordHash: 'dummy'
        });
        assert.fail('Should fail duplicate key');
      } catch (err) {
        assert.strictEqual(err.code, 11000);
      }
    });

    // 4. Garment Model Tests
    let createdGarment;
    await test('Garment Model: creates valid garment with default category and timestamps', async () => {
      createdGarment = await Garment.create({
        name: 'Classic Denim Jacket',
        description: 'Vintage blue denim jacket',
        category: 'jacket',
        imageUrl: '/uploads/sample_jacket.jpg',
        createdBy: createdUser._id
      });

      cleanup.garmentIds.push(createdGarment._id);
      assert.strictEqual(createdGarment.name, 'Classic Denim Jacket');
      assert.strictEqual(createdGarment.category, 'jacket');
      assert.strictEqual(createdGarment.createdBy.toString(), createdUser._id.toString());
      assert.ok(createdGarment.createdAt instanceof Date);
    });

    await test('Garment Model: enforces required name field', async () => {
      try {
        await Garment.create({ category: 'hoodie' });
        assert.fail('Should fail without name');
      } catch (err) {
        assert.ok(err.errors.name, 'Expected name validation error');
      }
    });

    // 5. TryOnHistory Model Tests
    let createdHistory;
    await test('TryOnHistory Model: creates valid record with default status pending', async () => {
      createdHistory = await TryOnHistory.create({
        user: createdUser._id,
        garment: createdGarment._id,
        personImageUrl: null,
        garmentImageUrl: null,
        resultImageUrl: null
      });

      cleanup.historyIds.push(createdHistory._id);
      assert.strictEqual(createdHistory.status, 'pending');
      assert.strictEqual(createdHistory.user.toString(), createdUser._id.toString());
      assert.strictEqual(createdHistory.garment.toString(), createdGarment._id.toString());
      assert.ok(createdHistory.createdAt instanceof Date);
    });

    await test('TryOnHistory Model: validates status enum', async () => {
      try {
        await TryOnHistory.create({
          status: 'invalid_status_value'
        });
        assert.fail('Should fail with invalid status');
      } catch (err) {
        assert.ok(err.errors.status, 'Expected status enum validation error');
      }
    });

    // 6. Garment CRUD API Endpoints
    let apiGarmentId;
    await test('POST /api/garments: creates a new garment via API (201 Created)', async () => {
      const res = await axios.post(`${BASE_URL}/api/garments`, {
        name: 'Summer Linen Shirt',
        description: 'Breathable white linen',
        category: 'shirt',
        imageUrl: '/uploads/linen_shirt.jpg'
      });

      assert.strictEqual(res.status, 201);
      assert.strictEqual(res.data.status, 'success');
      assert.strictEqual(res.data.data.name, 'Summer Linen Shirt');
      apiGarmentId = res.data.data._id;
      cleanup.garmentIds.push(apiGarmentId);
    });

    await test('POST /api/garments: rejects missing name with HTTP 400', async () => {
      try {
        await axios.post(`${BASE_URL}/api/garments`, { description: 'Missing name' });
        assert.fail('Should reject missing name');
      } catch (err) {
        assert.strictEqual(err.response.status, 400);
        assert.strictEqual(err.response.data.error, 'VALIDATION_ERROR');
      }
    });

    await test('GET /api/garments: lists garments with total count and filter', async () => {
      const res = await axios.get(`${BASE_URL}/api/garments?category=shirt`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'success');
      assert.ok(Array.isArray(res.data.data));
      assert.ok(res.data.total >= 1);
    });

    await test('GET /api/garments/:id: fetches single garment by ID', async () => {
      const res = await axios.get(`${BASE_URL}/api/garments/${apiGarmentId}`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.data._id, apiGarmentId);
    });

    await test('GET /api/garments/:id: rejects invalid ObjectId with HTTP 400', async () => {
      try {
        await axios.get(`${BASE_URL}/api/garments/not-a-valid-object-id`);
        assert.fail('Should reject invalid id');
      } catch (err) {
        assert.strictEqual(err.response.status, 400);
        assert.strictEqual(err.response.data.error, 'INVALID_ID');
      }
    });

    await test('PUT /api/garments/:id: updates garment details', async () => {
      const res = await axios.put(`${BASE_URL}/api/garments/${apiGarmentId}`, {
        name: 'Updated Summer Linen Shirt',
        category: 'top'
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.data.name, 'Updated Summer Linen Shirt');
      assert.strictEqual(res.data.data.category, 'top');
    });

    await test('DELETE /api/garments/:id: deletes garment', async () => {
      const res = await axios.delete(`${BASE_URL}/api/garments/${apiGarmentId}`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'success');

      // Verify deletion
      try {
        await axios.get(`${BASE_URL}/api/garments/${apiGarmentId}`);
        assert.fail('Should return 404');
      } catch (err) {
        assert.strictEqual(err.response.status, 404);
      }
    });

    // 7. Try-On History API Endpoints
    let apiHistoryId;
    await test('POST /api/history: records a try-on event (201 Created)', async () => {
      const res = await axios.post(`${BASE_URL}/api/history`, {
        user: createdUser._id.toString(),
        garment: createdGarment._id.toString(),
        status: 'completed',
        processingTimeMs: 380
      });

      assert.strictEqual(res.status, 201);
      assert.strictEqual(res.data.status, 'success');
      assert.strictEqual(res.data.data.status, 'completed');
      assert.strictEqual(res.data.data.processingTimeMs, 380);
      apiHistoryId = res.data.data._id;
      cleanup.historyIds.push(apiHistoryId);
    });

    await test('GET /api/history: lists history sorted by createdAt DESC', async () => {
      const res = await axios.get(`${BASE_URL}/api/history`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'success');
      assert.ok(Array.isArray(res.data.data));
      assert.ok(res.data.total >= 1);

      // Verify DESC sort
      if (res.data.data.length > 1) {
        const d1 = new Date(res.data.data[0].createdAt).getTime();
        const d2 = new Date(res.data.data[1].createdAt).getTime();
        assert.ok(d1 >= d2, 'History must be sorted descending by createdAt');
      }
    });

    await test('GET /api/history/:id: retrieves populated history entry', async () => {
      const res = await axios.get(`${BASE_URL}/api/history/${apiHistoryId}`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.data._id, apiHistoryId);
      assert.strictEqual(res.data.data.status, 'completed');
    });

    await test('DELETE /api/history/:id: deletes history entry', async () => {
      const res = await axios.delete(`${BASE_URL}/api/history/${apiHistoryId}`);
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.data.status, 'success');

      try {
        await axios.get(`${BASE_URL}/api/history/${apiHistoryId}`);
        assert.fail('Should return 404');
      } catch (err) {
        assert.strictEqual(err.response.status, 404);
      }
    });

  } finally {
    // Clean up test documents in MongoDB Atlas
    console.log('\n[*] Cleaning up test database artifacts...');
    try {
      if (cleanup.historyIds.length) {
        await TryOnHistory.deleteMany({ _id: { $in: cleanup.historyIds } });
      }
      if (cleanup.garmentIds.length) {
        await Garment.deleteMany({ _id: { $in: cleanup.garmentIds } });
      }
      if (cleanup.userIds.length) {
        await User.deleteMany({ _id: { $in: cleanup.userIds } });
      }
      console.log('    Cleaned up all temporary test records.');
    } catch (cleanErr) {
      console.warn('    Warning during cleanup:', cleanErr.message);
    }

    if (server) {
      server.close();
    }
    await disconnectDatabase();
  }

  console.log('\n====================================================');
  console.log(` DATABASE TEST SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('====================================================');

  if (failed > 0) {
    process.exit(1);
  }
}

runDatabaseTests().catch((err) => {
  console.error('Fatal test error:', err);
  if (server) server.close();
  disconnectDatabase();
  process.exit(1);
});
