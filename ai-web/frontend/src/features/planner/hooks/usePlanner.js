import { useCallback, useEffect, useState } from 'react';

import { get, post } from '../../../lib/api';

const DEFAULT_PAYLOAD = {
  goal: 'Launch the upgraded stack',
  audience_role: 'Instructor',
  audience_experience: 'intermediate',
  primary_risk: 'Student laptops differ from container setup',
};

export function usePlanner() {
  const [payload, setPayload] = useState(DEFAULT_PAYLOAD);
  const [plan, setPlan] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateField = useCallback((field, value) => {
    setPayload((prev) => ({ ...prev, [field]: value }));
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const records = await get('/planner/plan/history');
      setHistory(records);
    } catch (err) {
      console.error('Failed to fetch plan history', err);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const submit = useCallback(async (event) => {
    event?.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await post('/planner/plan', payload);
      setPlan(response);
      loadHistory();
    } catch (err) {
      console.error('Plan generation failed', err);
      setError(err.message || 'Unable to generate plan');
    } finally {
      setLoading(false);
    }
  }, [payload, loadHistory]);

  return { payload, plan, history, loading, error, updateField, submit };
}

