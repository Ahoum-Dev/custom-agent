import type { NextApiRequest, NextApiResponse } from 'next';

interface CallRecord {
  id: number;
  session_id: string;
  facilitator_name: string;
  facilitator_phone: string;
  call_start_time: string;
  call_end_time?: string;
  call_duration_seconds?: number;
  call_status: string;
  outcome?: string;
  notes?: string;
  callback_requested: boolean;
  callback_time?: string;
}

// Mock data for development - replace with actual database queries in production
const mockCalls: CallRecord[] = [
  {
    id: 1,
    session_id: 'session_001',
    facilitator_name: 'John Smith',
    facilitator_phone: '+1234567890',
    call_start_time: new Date(Date.now() - 3600000).toISOString(),
    call_end_time: new Date(Date.now() - 3300000).toISOString(),
    call_duration_seconds: 300,
    call_status: 'completed',
    outcome: 'interested',
    notes: 'Very enthusiastic about joining the platform',
    callback_requested: false,
  },
  {
    id: 2,
    session_id: 'session_002',
    facilitator_name: 'Jane Doe',
    facilitator_phone: '+1987654321',
    call_start_time: new Date(Date.now() - 7200000).toISOString(),
    call_end_time: new Date(Date.now() - 6900000).toISOString(),
    call_duration_seconds: 180,
    call_status: 'completed',
    outcome: 'callback_requested',
    notes: 'Needs more time to consider',
    callback_requested: true,
    callback_time: new Date(Date.now() + 86400000).toISOString(),
  },
  {
    id: 3,
    session_id: 'session_003',
    facilitator_name: 'Mike Johnson',
    facilitator_phone: '+1555123456',
    call_start_time: new Date(Date.now() - 1800000).toISOString(),
    call_duration_seconds: 45,
    call_status: 'failed',
    outcome: 'no_answer',
    notes: 'Call went to voicemail',
    callback_requested: false,
  },
  {
    id: 4,
    session_id: 'session_004',
    facilitator_name: 'Sarah Wilson',
    facilitator_phone: '+1444987654',
    call_start_time: new Date().toISOString(),
    call_status: 'in-progress',
    callback_requested: false,
  },
];

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // In production, this would query your PostgreSQL database
    // Example query:
    // const calls = await db.query(`
    //   SELECT * FROM call_transcripts 
    //   ORDER BY call_start_time DESC 
    //   LIMIT 100
    // `);

    // For now, return mock data
    const sortedCalls = mockCalls.sort((a, b) => 
      new Date(b.call_start_time).getTime() - new Date(a.call_start_time).getTime()
    );

    res.status(200).json(sortedCalls);
  } catch (error) {
    console.error('Error fetching calls:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
}
