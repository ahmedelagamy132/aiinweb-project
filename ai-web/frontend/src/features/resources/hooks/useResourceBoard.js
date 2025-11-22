import { useCallback, useEffect, useState } from 'react';

import { get, post } from '../../../lib/api';

const EMPTY = {
  title: 'Postgres quickstart',
  description: 'Capture your own tips and share links with the cohort.',
  url: 'https://example.com',
  difficulty: 'intermediate',
};

export function useResourceBoard() {
  const [form, setForm] = useState(EMPTY);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadResources = useCallback(async () => {
    try {
      const items = await get('/resources/');
      setResources(items);
    } catch (err) {
      console.error('Failed to load resources', err);
      setError('Unable to fetch resources');
    }
  }, []);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  const updateForm = useCallback((field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  }, []);

  const submit = useCallback(async (event) => {
    event?.preventDefault();
    setLoading(true);
    setError('');
    try {
      await post('/resources/', form);
      setForm(EMPTY);
      loadResources();
    } catch (err) {
      console.error('Failed to save resource', err);
      setError(err.message || 'Unable to save');
    } finally {
      setLoading(false);
    }
  }, [form, loadResources]);

  return { form, updateForm, submit, resources, loading, error };
}

