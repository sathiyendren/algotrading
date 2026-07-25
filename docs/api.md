# FII Algo Trading API Documentation

## Base URL


## Authentication
Currently no authentication required (for development).

## Endpoints

### 1. Health Check
Check if the API server is running.

**Endpoint:** 

**Response:**


### 2. System Status
Get current system status and metrics.

**Endpoint:** 

**Response:**


### 3. Market Data
Get current market data.

**Endpoint:** 

**Response:**


### 4. Recent Signals
Get recent trading signals.

**Endpoint:** 

**Query Parameters:**
-  (optional): Number of signals to return (default: 10)

**Response:**


### 5. Generate Signal
Generate a new trading signal.

**Endpoint:** 

**Response:**


### 6. Active Positions
Get current active positions.

**Endpoint:** 

**Response:**


### 7. Position Details
Get details of a specific position.

**Endpoint:** 

**Response:**


### 8. Close Position
Close a specific position.

**Endpoint:** 

**Response:**


### 9. P&L Summary
Get profit and loss summary.

**Endpoint:** 

**Response:**


### 10. Risk Metrics
Get current risk metrics.

**Endpoint:** 

**Response:**


### 11. Performance Metrics
Get performance statistics.

**Endpoint:** 

**Response:**


## Error Responses

All endpoints return appropriate HTTP status codes:

-  - Success
-  - Bad Request
-  - Not Found
-  - Internal Server Error

Error response format:


## Rate Limiting

Currently no rate limiting implemented (development mode).

## WebSocket Support

WebSocket endpoints for real-time data will be added in future versions.

## Integration Examples

### Python Example


### JavaScript Example

