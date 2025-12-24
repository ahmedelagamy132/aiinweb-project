import PropTypes from 'prop-types';

/**
 * EchoForm - A form component demonstrating retry patterns.
 */
export function EchoForm({
    message,
    setMessage,
    response,
    pending,
    error,
    retryCount,
    submit,
}) {
    return (
        <div>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    submit();
                }}
                className="form"
            >
                <div className="form-group">
                    <label htmlFor="echoMessage">Message</label>
                    <input
                        type="text"
                        id="echoMessage"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Enter a message to echo..."
                    />
                </div>

                <button type="submit" disabled={pending}>
                    {pending
                        ? `Retrying... (Attempt ${retryCount})`
                        : 'Send Echo'}
                </button>
            </form>

            {error && <div className="alert alert-error">{error}</div>}

            {response && (
                <div className="content-box">
                    <h3>✅ Response</h3>
                    <p><strong>Message:</strong> {response.message}</p>
                    <p><strong>Echo:</strong> {response.echo}</p>
                    <p className="text-secondary">Completed after {response.attempts} attempt(s)</p>
                </div>
            )}
        </div>
    );
}

EchoForm.propTypes = {
    message: PropTypes.string.isRequired,
    setMessage: PropTypes.func.isRequired,
    response: PropTypes.object,
    pending: PropTypes.bool.isRequired,
    error: PropTypes.string.isRequired,
    retryCount: PropTypes.number.isRequired,
    submit: PropTypes.func.isRequired,
};
