import { useCallback, useState } from 'react';
import { post } from '../../../lib/api';
import { withRetry } from '../../../lib/retry';

/**
 * Hook for managing the echo form state with retry logic.
 */
export function useEchoForm() {
    const [message, setMessage] = useState('');
    const [response, setResponse] = useState(null);
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');
    const [retryCount, setRetryCount] = useState(0);

    const submit = useCallback(async () => {
        if (!message.trim()) {
            setError('Please enter a message');
            return;
        }

        setPending(true);
        setError('');
        setResponse(null);
        setRetryCount(0);

        const clientKey = `echo-${Date.now()}`;

        try {
            const result = await withRetry(
                async () => {
                    setRetryCount((prev) => prev + 1);
                    return post('/echo', { message, client_key: clientKey });
                },
                3,
                500
            );
            setResponse(result);
        } catch (err) {
            console.error('Echo request failed', err);
            setError(err.message || 'Request failed after retries');
        } finally {
            setPending(false);
        }
    }, [message]);

    return {
        message,
        setMessage,
        response,
        pending,
        error,
        retryCount,
        submit,
    };
}
