# SysSight Frontend - Documentation

## Overview

The SysSight Frontend is a React-based single-page application that provides a real-time monitoring dashboard for system metrics across multiple hosts. It features interactive graphs, metric tables, process management, and alert monitoring.

### Key Technologies
- **React 19**: Modern UI library with hooks
- **TypeScript**: Type-safe development
- **Chart.js**: Graph rendering with `react-chartjs-2`
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool and dev server

### Architecture
- **Single-Page Application (SPA)**: Two main pages (Dashboard, Alerts)
- **Component-Based**: Reusable, modular components
- **API-Driven**: All data fetched from backend REST API
- **Real-Time Updates**: Polling for latest metrics

---

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client functions
│   │   ├── client.ts     # Base API request utility
│   │   ├── hosts.ts      # Host & metrics endpoints
│   │   ├── alerts.ts     # Alert management endpoints
│   │   └── thresholds.ts  # Threshold configuration
│   ├── components/        # React components
│   │   ├── GraphView.tsx        # Line chart component
│   │   ├── GraphFilters.tsx     # Date range picker
│   │   ├── MetricsTable.tsx     # Current metrics table
│   │   ├── HostBar.tsx          # Host selection tabs
│   │   ├── ProcessTable.tsx      # Process list
│   │   ├── AlertTable.tsx       # Alert list
│   │   ├── AlertStats.tsx       # Alert statistics
│   │   └── ThresholdSettings.tsx # Threshold config UI
│   ├── pages/            # Page components
│   │   ├── DashboardPage.tsx
│   │   └── AlertsPage.tsx
│   ├── types/            # TypeScript definitions
│   │   └── index.ts
│   ├── App.tsx           # Main app with navigation
│   └── main.tsx          # Entry point
└── package.json
```

---

## API Client Architecture

### Base API Client (`src/api/client.ts`)

The core API request utility that all endpoints use.

```typescript
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function apiRequest<T>(
  endpoint: string,
  method: string = 'GET',
  body?: any
): Promise<T>
```

**Features**:
- Generic type parameter `<T>` for type-safe responses
- Automatic JSON serialization
- Error handling with custom `ApiError` class
- Environment-based API URL configuration

**Error Handling**:
```typescript
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string)
}
```

**Usage**:
```typescript
const data = await apiRequest<HostSummary[]>('/api/v1/hosts')
```

### Host API (`src/api/hosts.ts`)

Endpoints for fetching host data and metrics.

#### `getHosts()`
```typescript
export async function getHosts(): Promise<HostSummary[]>
```

**Endpoint**: `GET /api/v1/hosts`

**Returns**: Array of host summaries with status (online/offline)

**Data Structure**:
```typescript
interface HostSummary {
  host_id: string
  ip_address: string
  status: 'online' | 'offline'
  last_seen: string
}
```

#### `getLatestMetrics(hostId: string)`
```typescript
export async function getLatestMetrics(hostId: string): Promise<LatestMetrics>
```

**Endpoint**: `GET /api/v1/hosts/{hostId}/metrics/latest`

**Response Transformation**:
The backend returns a nested structure, but the frontend expects a flat structure. The function transforms:
```typescript
// Backend response
{
  memory_percent: 62.1,
  disk_usage: { "/": { percent: 78.5 } },
  network: { bytes_sent: 123456, bytes_recv: 987654 },
  load_average: [1.23, 2.45, 3.67]
}

// Transformed to
{
  mem_percent_used: 62.1,
  disk_percent_used: 78.5,
  network_bytes_sent: 123456,
  network_bytes_recv: 987654,
  load_avg_1m: 1.23,
  load_avg_5m: 2.45,
  load_avg_15m: 3.67
}
```

**Polling**: Called every 10 seconds to keep data fresh

#### `getHistoricalMetrics(hostId, metric, from, to, step)`
```typescript
export async function getHistoricalMetrics(
  hostId: string,
  metric: string,
  from: string,
  to: string,
  step: string = '1m'
): Promise<HistoricalSeries>
```

**Endpoint**: `GET /api/v1/hosts/{hostId}/metrics/historical/{metric}?start_time=...&end_time=...&step=...`

**Timestamp Conversion**:
- Input: HTML5 `datetime-local` format (no timezone)
- Output: ISO 8601 with 'Z' suffix (UTC)
- Converts to Unix timestamps for API

**Response Transformation**:
```typescript
// Backend response
{
  metric_type: "cpu_percent",
  values: [
    [1704067200, 45.2],  // [timestamp, value]
    [1704067260, 46.1]
  ]
}

// Transformed to
{
  metric: "cpu_percent",
  data: [
    { timestamp: "2024-01-01T12:00:00.000Z", value: 45.2 },
    { timestamp: "2024-01-01T12:01:00.000Z", value: 46.1 }
  ]
}
```

**Why**: Chart.js expects ISO timestamps, backend uses Unix epoch

#### `getProcesses(hostId, page, limit, sortBy, sortOrder)`
```typescript
export async function getProcesses(...): Promise<ProcessListResponse>
```

**Endpoint**: `GET /api/v1/hosts/{hostId}/processes?page=...&limit=...&sort_by=...&sort_order=...`

**Pagination**: Server-side pagination with page, limit, total_pages

**Sorting**: Supports CPU %, Memory %, PID, Name

---

## Graph Rendering (Chart.js)

### Chart.js Setup (`src/components/GraphView.tsx`)

The graph component uses **react-chartjs-2** and **Chart.js**.

#### Registration
```typescript
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, TimeScale)
```

**Why These Modules**:
- `CategoryScale`: X-axis for timestamps
- `LinearScale`: Y-axis for metric values
- `LineElement`: Line drawing
- `PointElement`: Points on line (disabled with `pointRadius: 0`)
- `Tooltip`: Hover tooltips
- `Legend`: Line labels
- `TimeScale`: **Not used** (plain category scale used instead)

### Graph Component Structure

#### Props
```typescript
type Props = {
  historicalData: HistoricalSeries | null
  from?: string
  to?: string
}
```

#### Data Filtering

**Date Range Filtering**:
```typescript
let filteredData = historicalData.data
if (from && to) {
  const parseUtc = (s: string) => {
    const str = s.endsWith('Z') || s.includes('+') ? s : `${s}:00Z`.replace(' ', 'T')
    return new Date(str).getTime()
  }
  
  let fromTime = parseUtc(from)
  let toTime = parseUtc(to)
  
  // Fix reversed dates
  if (fromTime > toTime) [fromTime, toTime] = [toTime, fromTime]
  
  filteredData = historicalData.data.filter(point => {
    const pointTime = new Date(point.timestamp).getTime()
    return pointTime >= fromTime && pointTime <= toTime
  })
}
```

**Why Client-Side Filtering**: Simpler than modifying API calls on every filter change

**Edge Cases Handled**:
- Reversed date ranges (from > to)
- Timestamp format variations (UTC, timezone offset)
- No data in selected range

#### Chart Data Structure

```typescript
const labels = filteredData.map(point => point.timestamp)
const data = filteredData.map(point => point.value)

const chartData = {
  labels,  // X-axis values (timestamps)
  datasets: [{
    label: historicalData.metric,
    data,  // Y-axis values (metric values)
    borderColor: 'rgb(37, 99, 235)',  // Blue line
    backgroundColor: 'rgba(37, 99, 235, 0.3)',  // Light blue fill
    pointRadius: 0,  // Hide points (cleaner look)
    tension: 0.3,  // Smooth curves
  }]
}
```

**Key Settings**:
- `pointRadius: 0`: No visible points on line
- `tension: 0.3`: Smooth Bezier curves
- `backgroundColor`: Semi-transparent fill under line
- `borderColor`: Blue line color (Tailwind blue-600)

#### Chart Options

```typescript
const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },  // No legend for single-line graphs
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: { ticks: { maxTicksLimit: 6 } },  // Max 6 X-axis labels
    y: { beginAtZero: true },
  }
}
```

**Options Breakdown**:
- `responsive`: Adapts to container size
- `maintainAspectRatio: false`: Uses full container height
- `legend: display: false`: No legend for single metric
- `mode: 'index'`: Show tooltip near any point
- `intersect: false`: Easier to hover
- `maxTicksLimit: 6`: Limits X-axis labels for readability
- `beginAtZero: true`: Y-axis starts at 0

#### Rendering

```typescript
<Line 
  key={`${historicalData.metric}|${from}|${to}|${labels.length}`}
  data={chartData} 
  options={options} 
/>
```

**Why Key Prop**: Forces Chart.js to re-render when data changes
- Changes on: metric type, date range, data point count
- Key format: `"cpu_percent|2024-01-01T00:00|2024-01-01T23:59|120"`

**Container**:
```typescript
<div className="rounded-md border border-gray-200 bg-white p-3 h-64">
  <div className="font-medium mb-2">{historicalData.metric}</div>
  <Line ... />
</div>
```

- `h-64`: Fixed height (256px)
- `maintainAspectRatio: false`: Chart fills height

---

## Data Flow

### Dashboard Page Flow

```
User loads DashboardPage
    ↓
useEffect triggers (empty deps)
    ↓
getHosts() → GET /api/v1/hosts
    ↓
setHosts(hosts) → Update state
    ↓
useEffect (auto-select first host)
    ↓
setSelectedHostId(hosts[0].host_id)
    ↓
useEffect triggers (selectedHostId changes)
    ↓
getLatestMetrics(hostId) → GET /api/v1/hosts/{id}/metrics/latest
    ↓
setLatestMetrics(data)
    ↓
setInterval(fetchLatest, 10000)  // Poll every 10s
    ↓
User selects a metric (click "Graph" button)
    ↓
setSelectedMetric(metric)
    ↓
useEffect triggers (selectedMetric changes)
    ↓
getHistoricalMetrics(hostId, metric, from, to)
    ↓
GET /api/v1/hosts/{id}/metrics/historical/{metric}?...
    ↓
setHistoricalData(data)
    ↓
GraphView renders chart
```

### Alert Page Flow

```
User loads AlertsPage
    ↓
useEffect triggers (empty deps)
    ↓
getAlertStats() → GET /api/v1/alerts/stats
    ↓
setAlertStats(data)
    ↓
getThresholds() → GET /api/v1/thresholds
    ↓
setThresholds(data)
    ↓
getAlerts(filters) → GET /api/v1/alerts?hostname=...&status=...
    ↓
setAlerts(data)
    ↓
User changes filter
    ↓
setFilters(newFilters)
    ↓
getAlerts(newFilters)  // Re-fetch with new filters
```

---

## Components Overview

### DashboardPage

**Location**: `src/pages/DashboardPage.tsx`

**State Management**:
- `hosts`: List of available hosts
- `selectedHostId`: Currently selected host
- `selectedMetric`: Currently selected metric for graphing
- `latestMetrics`: Current values for selected host
- `historicalData`: Time-series data for graphing
- `alertStats`: Alert summary statistics
- `range`: Date range for graph (`{ from, to }`)

**Effects**:
1. **Mount**: Fetch hosts, fetch alert stats
2. **Auto-select**: Select first host when hosts loaded
3. **Clear metric**: Reset selected metric when host changes
4. **Poll latest**: Fetch latest metrics every 10 seconds
5. **Fetch historical**: Fetch graph data when metric/date changes

**Key Features**:
- Host selection tab bar
- Latest metrics table with "Graph" buttons
- Interactive time-series graph
- Process list for selected host
- Date range filtering

### AlertsPage

**Location**: `src/pages/AlertsPage.tsx`

**State Management**:
- `filters`: Current filter values (hostname, status, severity)

**Key Features**:
- Alert statistics cards
- Threshold configuration UI
- Filter form (hostname, status, severity)
- Alert table with pagination
- Alert resolution buttons

### GraphView

**Location**: `src/components/GraphView.tsx`

**Props**:
- `historicalData`: Time-series data to render
- `from`: Start timestamp (optional)
- `to`: End timestamp (optional)

**Features**:
- Chart.js Line chart
- Date range filtering
- Empty state handling
- Responsive design

**Empty States**:
```typescript
// No data available
if (!historicalData) {
  return <div>Select a metric to view its historical chart.</div>
}

// No data in range
if (!filteredData.length) {
  return <div>No data in selected date range.</div>
}
```

### MetricsTable

**Location**: `src/components/MetricsTable.tsx`

**Props**:
- `latestMetrics`: Current metric values
- `onSelectMetric`: Callback when "Graph" clicked

**Table Structure**:
- Rows for: CPU %, Memory %, Disk %, Network (sent/received), Load (1m/5m/15m)
- "Graph" button per row to select metric for graphing

**Metric Mapping**:
```typescript
const metricKeyMap = {
  cpu_percent: 'cpu_percent',
  mem_percent_used: 'mem_percent_used',
  disk_percent_used: 'disk_percent_used',
  // ... etc
}
```

### GraphFilters

**Location**: `src/components/GraphFilters.tsx`

**Props**:
- `from`: Start timestamp
- `to`: End timestamp
- `onChange`: Callback with new range

**UI**: Two `<input type="datetime-local">` controls

**Initial Range**: Last 1 hour (set in DashboardPage state)

### HostBar

**Location**: `src/components/HostBar.tsx`

**Props**:
- `hosts`: List of hosts
- `selectedHostId`: Active host
- `onSelect`: Host selection callback

**Features**: Tab-like buttons for each host with active state

---

## State Management

### No Global State Library

The app uses **React hooks** for state management:
- `useState`: Local component state
- `useEffect`: Side effects and data fetching
- Props drilling for parent-child communication

**Why No Redux/Zustand**: Simple app with minimal shared state

### State Location

**Dashboard Page State**:
- Host list (fetched once, static)
- Selected host (user interaction)
- Selected metric (user interaction)
- Latest metrics (polled every 10s)
- Historical data (fetched on demand)
- Alert stats (fetched on mount)
- Date range (user interaction)

**Alerts Page State**:
- Alert list (fetched on demand)
- Alert stats (fetched on mount)
- Thresholds (fetched on mount)
- Filters (user interaction)

### Data Synchronization

**Polling Strategy**:
```typescript
useEffect(() => {
  const fetchLatest = () => {
    getLatestMetrics(selectedHostId)
      .then(setLatestMetrics)
  }
  
  fetchLatest()  // Fetch immediately
  const interval = setInterval(fetchLatest, 10000)  // Then every 10s
  
  return () => clearInterval(interval)  // Cleanup
}, [selectedHostId])
```

**Why Polling**: Simple, works well for real-time dashboards

**Alternative**: WebSockets (not implemented, could be added)

---

## API Request Patterns

### Standard Fetch Pattern

```typescript
// 1. Build URL with query parameters
const params = new URLSearchParams({
  page: page.toString(),
  limit: limit.toString()
})
if (hostname) params.append('hostname', hostname)

// 2. Make request
const data = await apiRequest<ResponseType>(
  `/api/v1/endpoint?${params}`,
  'GET'
)

// 3. Transform if needed
return transformed(data)
```

### Error Handling

```typescript
try {
  const data = await getHosts()
  setHosts(data)
} catch (error) {
  console.error('Failed to fetch hosts:', error)
  // UI shows loading or error state
}
```

**Current**: Errors logged to console

**Future Enhancement**: Error toast notifications

### Authentication

**Not Implemented**: Current API doesn't require auth tokens

**Future**: Add Bearer token header:
```typescript
options.headers['Authorization'] = `Bearer ${token}`
```

---

## Graph Rendering Details

### Chart.js Setup

**Registration Order**:
1. Core modules (CategoryScale, LinearScale)
2. Elements (PointElement, LineElement)
3. Plugins (Tooltip, Legend)
4. Scale (TimeScale - registered but not used)

**Why TimeScale Not Used**: Current implementation uses CategoryScale for simplicity

### Data Format

**Input**: Array of `{ timestamp: ISO string, value: number }`

**Chart.js Format**:
```typescript
{
  labels: ["2024-01-01T12:00:00Z", "2024-01-01T12:01:00Z", ...],
  datasets: [{
    label: "cpu_percent",
    data: [45.2, 46.1, ...]
  }]
}
```

### Rendering Performance

**Key Prop Optimization**:
```typescript
<Line 
  key={`${metric}|${from}|${to}|${labels.length}`}
  ...
/>
```

- Forces full re-render on data change
- Prevents stale data
- Chart.js updates chart with new data

**Alternative**: Update chart data object directly (more complex)

### Styling

**Colors**: Blue theme (Tailwind blue-600)
```typescript
borderColor: 'rgb(37, 99, 235)',
backgroundColor: 'rgba(37, 99, 235, 0.3)'
```

**Curves**: Smooth Bezier curves with `tension: 0.3`

**Points**: Hidden with `pointRadius: 0`

**Fill**: Semi-transparent area under line

### Responsive Behavior

**Container**: Fixed height (`h-64` = 256px)

**Chart**: Adapts to container width

**Max Labels**: 6 X-axis labels to prevent crowding

---

## TypeScript Types

### Type Definitions (`src/types/index.ts`)

#### HostSummary
```typescript
interface HostSummary {
  host_id: string
  ip_address: string
  status: 'online' | 'offline'
  last_seen: string
}
```

#### LatestMetrics
```typescript
interface LatestMetrics {
  host_id: string
  timestamp: string
  cpu_percent: number
  mem_percent_used: number
  disk_percent_used: number
  network_bytes_sent: number
  network_bytes_recv: number
  load_avg_1m: number
  load_avg_5m: number
  load_avg_15m: number
  processes: number
  uptime_seconds: number
}
```

#### HistoricalSeries
```typescript
interface HistoricalSeries {
  metric: string
  data: HistoricalPoint[]
}

interface HistoricalPoint {
  timestamp: string
  value: number
}
```

#### Alert
```typescript
interface Alert {
  id: number
  hostname: string
  metric_name: string
  metric_value: number
  threshold_value: number
  severity: 'info' | 'warning' | 'critical'
  status: 'active' | 'resolved' | 'acknowledged'
  message: string
  triggered_at: string
  resolved_at: string | null
  resolved_by: string | null
}
```

**Union Types**: Used for constrained values (status, severity)

**Type Safety**: Prevents invalid values, enables autocomplete

---

## Build & Development

### Vite Configuration

**Dev Server**:
```bash
npm run dev
```

- Port: 5173 (default)
- HMR (Hot Module Reload): Fast updates during development
- TypeScript compilation on-the-fly

### Build

```bash
npm run build
```

**Output**: `dist/` folder with static files

### Scripts

```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "preview": "vite preview",
  "lint": "eslint ."
}
```

### Environment Variables

**File**: `.env`

```env
VITE_API_BASE=http://localhost:8000
```

**Usage**:
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
```

**Note**: `VITE_` prefix required for Vite to expose to client

---

## Key Features

### 1. Real-Time Updates

- Latest metrics polled every 10 seconds
- No page refresh required
- Alert stats updated periodically

### 2. Interactive Graphs

- Select any metric to view historical data
- Date range filtering
- Smooth curves with Chart.js
- Responsive design

### 3. Host Management

- Switch between multiple hosts
- Online/offline status indicators
- Host-specific metrics and processes

### 4. Alert Management

- Filter by hostname, status, severity
- View alert statistics
- Resolve alerts
- Configure thresholds

### 5. Process Viewing

- Paginated process list
- Sort by CPU, Memory, PID, Name
- Real-time process data from agents

---

## Future Enhancements

### Suggested Improvements

1. **WebSocket Support**: Real-time updates without polling
2. **Error Boundaries**: Better error handling with React Error Boundaries
3. **Loading States**: Skeleton screens while fetching data
4. **Toast Notifications**: User feedback for actions
5. **Export Charts**: Download charts as PNG/PDF
6. **Multiple Metrics**: Show multiple lines on same graph
7. **Dark Mode**: Toggle dark/light theme
8. **Responsive Tables**: Better mobile experience
9. **Metric Comparison**: Compare hosts side-by-side
10. **Alert Rules**: Create custom alert rules

---

## Summary

The SysSight Frontend is a modern React application that provides:
- **Interactive Monitoring Dashboard** with real-time updates
- **Chart.js-powered Graphs** for historical metric visualization
- **Alert Management** with filtering and resolution
- **Process Monitoring** with pagination and sorting
- **API-Driven Architecture** with type-safe TypeScript
- **Clean UI** with Tailwind CSS

The architecture prioritizes simplicity and maintainability while providing a rich user experience for system monitoring.

