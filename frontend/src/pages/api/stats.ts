import type { NextApiRequest, NextApiResponse } from 'next';

interface CallStats {
  total_calls: number;
  completed_calls: number;
  pending_calls: number;
  failed_calls: number;
  average_duration: number;
  success_rate: number;
}

// Mock data for development - replace with actual database queries in production
const generateMockStats = (): CallStats => {
  const total_calls = 127;
  const completed_calls = 89;
  const pending_calls = 23;
  const failed_calls = 15;
  const average_duration = 240; // seconds
  const success_rate = completed_calls / total_calls;

  return {
    total_calls,
    completed_calls,
    pending_calls,
    failed_calls,
    average_duration,
    success_rate,
  };
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // In production, this would query your PostgreSQL database
    // Example queries:
    // const totalCalls = await db.query('SELECT COUNT(*) FROM call_transcripts');
    // const completedCalls = await db.query('SELECT COUNT(*) FROM call_transcripts WHERE call_status = ?', ['completed']);
    // const avgDuration = await db.query('SELECT AVG(call_duration_seconds) FROM call_transcripts WHERE call_status = ?', ['completed']);

    const stats = generateMockStats();
    res.status(200).json(stats);
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
}
