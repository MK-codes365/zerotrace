const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const mongoose = require('mongoose');
const Razorpay = require('razorpay');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

mongoose.connect(process.env.MONGODB_URI)
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

const licenseSchema = new mongoose.Schema({
  key: { type: String, required: true, unique: true },
  planId: { type: String, required: true },
  email: { type: String, required: true },
  status: { type: String, default: 'active' },
  maxActivations: { type: Number, default: 1 },
  currentActivations: { type: Number, default: 0 },
  createdAt: { type: Date, default: Date.now }
});

const License = mongoose.model('License', licenseSchema);

const telemetrySchema = new mongoose.Schema({
  filesWiped: { type: Number, required: true },
  bytesWiped: { type: Number, required: true },
  method: { type: String, required: true },
  createdAt: { type: Date, default: Date.now }
});

const Telemetry = mongoose.model('Telemetry', telemetrySchema);

const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID,
  key_secret: process.env.RAZORPAY_KEY_SECRET
});

function generateLicenseKey(planId) {
  const segments = [];
  const prefix = planId && planId.includes('enterprise') ? 'ZT-ENT' : 'ZT-PRO';
  segments.push(prefix);

  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  for (let s = 0; s < 3; s++) {
    let segment = '';
    for (let i = 0; i < 4; i++) {
      segment += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    segments.push(segment);
  }
  return segments.join('-');
}

app.post('/api/orders', async (req, res) => {
  try {
    const { amount, currency } = req.body;
    if (!amount) {
      return res.status(400).json({ error: 'Amount is required' });
    }

    const options = {
      amount: Math.round(amount),
      currency: currency || 'INR',
      receipt: `receipt_order_${Date.now()}`
    };

    const order = await razorpay.orders.create(options);
    res.json(order);
  } catch (error) {
    console.error('Order creation error:', error);
    res.status(500).json({ error: 'Failed to create order' });
  }
});

app.post('/api/verify', async (req, res) => {
  try {
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature, cart, email } = req.body;

    if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature || !email) {
      return res.status(400).json({ error: 'Missing details' });
    }

    const text = `${razorpay_order_id}|${razorpay_payment_id}`;
    const generated_signature = crypto
      .createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(text)
      .digest('hex');

    if (generated_signature !== razorpay_signature) {
      return res.status(400).json({ error: 'Payment signature verification failed' });
    }

    const keys = [];
    if (cart && Array.isArray(cart)) {
      for (const item of cart) {
        for (let q = 0; q < item.quantity; q++) {
          const keyString = generateLicenseKey(item.planId);
          const maxActs = item.planId.includes('enterprise') ? 5 : 1;

          await License.create({
            key: keyString,
            planId: item.planId,
            email: email,
            maxActivations: maxActs
          });

          keys.push({
            name: item.name,
            key: keyString
          });
        }
      }
    }

    res.json({
      success: true,
      keys: keys
    });
  } catch (error) {
    console.error('Signature verification error:', error);
    res.status(500).json({ error: 'Verification failed' });
  }
});

app.post('/api/activate', async (req, res) => {
  try {
    const { key } = req.body;
    if (!key) {
      return res.status(400).json({ error: 'License key is required' });
    }

    const license = await License.findOne({ key });
    if (!license) {
      return res.status(404).json({ error: 'License key not found' });
    }

    if (license.status !== 'active') {
      return res.status(400).json({ error: 'License is suspended or inactive' });
    }

    if (license.currentActivations >= license.maxActivations) {
      return res.status(400).json({ error: 'Max activation limit reached' });
    }

    license.currentActivations += 1;
    await license.save();

    res.json({
      success: true,
      message: 'License activated successfully',
      planId: license.planId,
      currentActivations: license.currentActivations,
      maxActivations: license.maxActivations
    });
  } catch (error) {
    console.error('License activation error:', error);
    res.status(500).json({ error: 'Activation failed' });
  }
});

app.post('/api/telemetry', async (req, res) => {
  try {
    const { filesWiped, bytesWiped, method } = req.body;
    if (filesWiped === undefined || bytesWiped === undefined || !method) {
      return res.status(400).json({ error: 'Missing parameters' });
    }

    await Telemetry.create({ filesWiped, bytesWiped, method });
    res.json({ success: true });
  } catch (error) {
    console.error('Telemetry logging error:', error);
    res.status(500).json({ error: 'Failed to record telemetry' });
  }
});

app.get('/api/stats', async (req, res) => {
  try {
    const aggregates = await Telemetry.aggregate([
      {
        $group: {
          _id: null,
          totalFiles: { $sum: '$filesWiped' },
          totalBytes: { $sum: '$bytesWiped' }
        }
      }
    ]);

    const dbFiles = aggregates[0]?.totalFiles || 0;
    const dbBytes = aggregates[0]?.totalBytes || 0;

    // Retrieve live count of active license key registrations
    const activeUsers = await License.countDocuments({ status: 'active' });

    res.json({
      filesWiped: dbFiles,
      bytesWiped: dbBytes,
      activeUsers: activeUsers
    });
  } catch (error) {
    console.error('Stats fetch error:', error);
    res.status(500).json({ error: 'Failed to load stats' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
