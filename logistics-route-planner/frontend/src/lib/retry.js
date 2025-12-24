/**
 * Retry helper that re-runs a promise-returning function when it fails.
 *
 * @param {Function} fn - Async function to retry
 * @param {number} attempts - Number of retry attempts (default: 2)
 * @param {number} delayMs - Delay between retries in ms (default: 400)
 * @returns {Promise<any>} Result from successful attempt
 */
export async function withRetry(fn, attempts = 2, delayMs = 400) {
    let lastError;
    for (let attempt = 0; attempt <= attempts; attempt += 1) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
        }
        if (attempt < attempts) {
            await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
    }
    throw lastError;
}
