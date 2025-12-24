import { useCallback, useEffect, useState } from 'react';
import { get, post } from '../../../lib/api';

/**
 * Hook for managing the route readiness agent state.
 * Provides functionality to run the agent, view history, and select routes.
 */
export function useAgent() {
    const [routes, setRoutes] = useState([]);
    const [selectedRoute, setSelectedRoute] = useState('');
    const [audienceRole, setAudienceRole] = useState('Driver');
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

    // Fetch available routes on mount
    useEffect(() => {
        async function loadRoutes() {
            try {
                const data = await get('/ai/routes');
                setRoutes(data.routes || []);
                if (data.routes?.length > 0) {
                    setSelectedRoute(data.routes[0].slug);
                    setAudienceRole(data.routes[0].audience_role);
                    if (data.routes[0].delivery_date) {
                        setLaunchDate(data.routes[0].delivery_date);
                    }
                }
            } catch (err) {
                console.error('Failed to load routes', err);
            }
        }
        loadRoutes();
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
    }, []);

    const runAgent = useCallback(async () => {
        if (!selectedRoute) {
            setError('Please select a route');
            return;
        }

        setPending(true);
        setError('');
        setResult(null);

        try {
            const response = await post('/ai/route-readiness', {
                route_slug: selectedRoute,
                launch_date: launchDate,
                audience_role: audienceRole,
                audience_experience: audienceExperience,
                include_risks: includeRisks,
            });
            setResult(response);
            loadHistory();
        } catch (err) {
            console.error('Agent request failed', err);
            setError(err.message || 'Failed to run agent');
        } finally {
            setPending(false);
        }
    }, [selectedRoute, launchDate, audienceRole, audienceExperience, includeRisks, loadHistory]);

    const selectRoute = useCallback((slug) => {
        setSelectedRoute(slug);
        const route = routes.find((r) => r.slug === slug);
        if (route) {
            setAudienceRole(route.audience_role);
            if (route.delivery_date) {
                setLaunchDate(route.delivery_date);
            }
        }
        setResult(null);
    }, [routes]);

    return {
        // Form state
        routes,
        selectedRoute,
        audienceRole,
        audienceExperience,
        includeRisks,
        launchDate,
        // Setters
        selectRoute,
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
