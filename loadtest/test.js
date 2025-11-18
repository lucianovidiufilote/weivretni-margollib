#!/usr/bin/env node
const autocannon = require('autocannon');

const target = process.env.TARGET || 'http://localhost:8000/records';
const duration = Number(process.env.DURATION || 10);
const connections = Number(process.env.CONNECTIONS || 30);
const rate = Number(process.env.RATE || 28);

const buildPayload = () => JSON.stringify({
  recordId: `load-${Date.now()}-${Math.random()}`,
  time: new Date().toISOString(),
  sourceId: 'loadtest',
  destinationId: 'loadtest-dest',
  type: 'positive',
  value: 120.45,
  unit: 'SEK',
  reference: 'loadtest-ref'
});

const instance = autocannon({
  url: target,
  duration,
  connections,
  overallRate: rate,
  headers: {
    'content-type': 'application/json'
  },
  requests: [
    {
      method: 'POST',
      setupRequest: (req) => {
        req.body = buildPayload();
        return req;
      }
    }
  ]
}, (err, res) => {
  if (err) {
    console.error('Autocannon failed', err);
    process.exit(1);
  }
  console.log('Load test finished');
  console.table({
    requestsPerSec: res.requests.average,
    latencyAvg: res.latency.average,
    errors: res.errors
  });
});

autocannon.track(instance, { renderProgressBar: true });
