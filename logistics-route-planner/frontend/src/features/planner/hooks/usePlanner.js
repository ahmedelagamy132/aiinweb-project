import { useCallback, useState } from 'react';
import { post, get } from '../../../lib/api';

/**
 * Hook for managing the planner form state.
 */
export function usePlanner() {
    const [goal, setGoal] = useState('Optimize express delivery route');
    const [audienceRole, setAudienceRole] = useState('Driver');
    const [audienceExperience, setAudienceExperience] = useState('intermediate');
    const [primaryRisk, setPrimaryRisk] = useState('');

    const [plan, setPlan] = useState(null);
    const [history, setHistory] = useState([]);
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');

    const loadHistory = useCallback(async () => {
        try {
            const data = await get('/planner/route/history');
            setHistory(data || []);
        } catch (err) {
            console.error('Failed to load history', err);
        }
    }, []);

    const submit = useCallback(async () => {
        if (!goal.trim()) {
            setError('Please enter a goal');
            return;
        }

        setPending(true);
        setError('');
        setPlan(null);

        try {
            const result = await post('/planner/route', {
                goal,
                audience_role: audienceRole,
                audience_experience: audienceExperience,
                primary_risk: primaryRisk || null,
            });
            setPlan(result);
            loadHistory();
        } catch (err) {
            console.error('Plan request failed', err);
            setError(err.message || 'Failed to generate plan');
        } finally {
            setPending(false);
        }
    }, [goal, audienceRole, audienceExperience, primaryRisk, loadHistory]);

    return {
        goal,
        setGoal,
        audienceRole,
        setAudienceRole,
        audienceExperience,
        setAudienceExperience,
        primaryRisk,
        setPrimaryRisk,
        plan,
        history,
        pending,
        error,
        submit,
    };
}
