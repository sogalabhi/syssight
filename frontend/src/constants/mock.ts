export type HostSummary = {
  host_id: string;
  hostname: string;
  ip_address: string;
  last_seen: string;
  status: 'online' | 'offline';
};

export const MOCK_HOSTS: HostSummary[] = [
  {
    host_id: 'server-alpha-01',
    hostname: 'server-alpha-01',
    ip_address: '192.168.1.10',
    last_seen: '2025-10-18T12:30:00Z',
    status: 'online',
  },
  {
    host_id: 'db-primary-01',
    hostname: 'db-primary-01',
    ip_address: '192.168.1.12',
    last_seen: '2025-10-18T11:00:00Z',
    status: 'offline',
  },
];

export type LatestMetrics = {
  host_id: string;
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_usage: { '/': { percent: number } };
  network: { bytes_sent: number; bytes_recv: number };
  load_average: [number, number, number];
};

export const MOCK_LATEST_BY_HOST: Record<string, LatestMetrics> = {
  'server-alpha-01': {
    host_id: 'server-alpha-01',
    timestamp: '2025-10-18T12:30:00Z',
    cpu_percent: 15.5,
    memory_percent: 45.2,
    disk_usage: { '/': { percent: 60.1 } },
    network: { bytes_sent: 102400, bytes_recv: 512000 },
    load_average: [0.5, 0.45, 0.4],
  },
  'db-primary-01': {
    host_id: 'db-primary-01',
    timestamp: '2025-10-18T12:30:00Z',
    cpu_percent: 23.1,
    memory_percent: 61.4,
    disk_usage: { '/': { percent: 72.3 } },
    network: { bytes_sent: 204800, bytes_recv: 300000 },
    load_average: [0.9, 0.7, 0.6],
  },
};

export type HistoricalSeries = {
  metric_type:
    | 'cpu_percent'
    | 'mem_percent_used'
    | 'disk_percent_used'
    | 'net_bytes_sent'
    | 'net_bytes_received'
    | 'load_1m'
    | 'load_5m'
    | 'load_15m';
  values: [number, number][];
};

export const MOCK_HISTORICAL_BY_HOST_METRIC: Record<string, HistoricalSeries> = {
  'server-alpha-01|cpu_percent': {
    metric_type: 'cpu_percent',
    values: [
      [1729188000, 20.5],
      [1729191600, 15.2],
      [1729195200, 12.8],
      [1729198800, 10.1],
      [1729202400, 9.5],
      [1729206000, 11.3],
      [1729209600, 25.8],
      [1729213200, 45.1],
      [1729216800, 55.6],
      [1729220400, 52.3],
      [1729224000, 48.9],
      [1729227600, 50.2],
      [1729231200, 47.7],
      [1729234800, 35.1],
      [1729238400, 30.5]
    ]
  },
  'server-alpha-01|mem_percent_used': {
    metric_type: 'mem_percent_used',
    values: [
      [1666094400, 42.0],
      [1666094460, 44.1],
      [1666094520, 45.2],
    ],
  },
};

export const ALLOWED_METRICS = [
  'cpu_percent',
  'mem_percent_used',
  'disk_percent_used',
  'net_bytes_sent',
  'net_bytes_received',
  'load_1m',
  'load_5m',
  'load_15m',
];


