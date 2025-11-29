import { useCallback, useEffect, useState } from 'react';

import { get, post } from '../../../lib/api';

/**
 * Hook for managing the release readiness agent state.
 * Provides functionality to run the agent, view history, and select features.
 */
export function useAgent() {
  const [features, setFeatures] = useState([]);
  const [selectedFeature, setSelectedFeature] = useState('');
  const [audienceRole, setAudienceRole] = useState('Instructor');
  const [audienceExperience, setAudienceExperience] = useState('intermediate');
  const [includeRisks, setIncludeRisks] = useState(true);
  const [launchDate, setLaunchDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() + 7);
    return date.toISOString().split('T')[0];
  });

  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');

  // Fetch available features on mount
  useEffect(() => {
    async function loadFeatures() {
      try {
        const data = await get('/ai/features');
        setFeatures(data.features || []);
        if (data.features?.length > 0) {
          setSelectedFeature(data.features[0].slug);
          setAudienceRole(data.features[0].audience_role);
          if (data.features[0].launch_date) {
            setLaunchDate(data.features[0].launch_date);
          }
        }
      } catch (err) {
        console.error('Failed to load features', err);
      }
    }
    loadFeatures();
  }, []);

  // Fetch history on mount and after running
  const loadHistory = useCallback(async () => {
    try {
      const data = await get('/ai/history?limit=5');
      setHistory(data.runs || []);
    } catch (err) {
      console.error('Failed to load history', err);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const runAgent = useCallback(async () => {
    if (!selectedFeature) {
      setError('Please select a feature');
      return;
    }

    setPending(true);
    setError('');
    setResult(null);

    try {
      const response = await post('/ai/release-readiness', {
        feature_slug: selectedFeature,
        launch_date: launchDate,
        audience_role: audienceRole,
        audience_experience: audienceExperience,
        include_risks: includeRisks,
      });
      setResult(response);
      loadHistory(); // Refresh history after running
    } catch (err) {
      console.error('Agent request failed', err);
      setError(err.message || 'Failed to run agent');
    } finally {
      setPending(false);
    }
  }, [selectedFeature, launchDate, audienceRole, audienceExperience, includeRisks, loadHistory]);

  const selectFeature = useCallback((slug) => {
    setSelectedFeature(slug);
    const feature = features.find((f) => f.slug === slug);
    if (feature) {
      setAudienceRole(feature.audience_role);
      if (feature.launch_date) {
        setLaunchDate(feature.launch_date);
      }
    }
    setResult(null);
  }, [features]);

  return {
    // Form state
    features,
    selectedFeature,
    audienceRole,
    audienceExperience,
    includeRisks,
    launchDate,
    // Setters
    selectFeature,
    setAudienceRole,
    setAudienceExperience,
    setIncludeRisks,
    setLaunchDate,
    // Actions
    runAgent,
    // Results
    result,
    history,
    pending,
    error,
  };
}
