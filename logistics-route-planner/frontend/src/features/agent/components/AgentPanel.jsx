import { useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import { Map, MapPin, Trash2, Send, Plus, Settings } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

/**
 * TypeScript-style interfaces (documented in comments for JS)
 * 
 * @typedef {Object} Stop
 * @property {string} stop_id - Unique identifier (S001, S002, etc.)
 * @property {string} location - Address or description
 * @property {number} lat - Latitude
 * @property {number} lng - Longitude
 * @property {number} sequence_number - Order in route (1, 2, 3...)
 * @property {string} [label] - Optional user-editable name
 * @property {string} [time_window_start] - Optional start time (HH:MM)
 * @property {string} [time_window_end] - Optional end time (HH:MM)
 * @property {string} priority - low | normal | high
 * 
 * @typedef {Object} OperationalConstraints
 * @property {number} [max_route_duration_hours] - Maximum route duration
 * @property {string} [driver_shift_end] - Shift end time (HH:MM)
 * @property {number} [vehicle_capacity] - Vehicle capacity limit
 * @property {string} [notes] - Additional notes
 * 
 * @typedef {Object} RouteRequest
 * @property {string} route_id - Unique route identifier
 * @property {string} start_location - Depot or warehouse
 * @property {string} planned_start_time - ISO8601 datetime string
 * @property {string} [vehicle_id] - Vehicle identifier
 * @property {Stop[]} stops - List of delivery stops
 * @property {OperationalConstraints} [constraints] - Optional constraints
 * @property {string} task - validate_route | optimize_route | validate_and_recommend
 */

// Component for handling map clicks and adding markers
function MapClickHandler({ onMapClick }) {
    useMapEvents({
        click: (e) => {
            onMapClick(e.latlng);
        },
    });
    return null;
}

// Helper functions for tool display
function getToolIcon(toolName) {
    const lowerName = toolName.toLowerCase();
    if (lowerName.includes('weather')) return '🌤️';
    if (lowerName.includes('metric') || lowerName.includes('calculate')) return '📊';
    if (lowerName.includes('timing') || lowerName.includes('validate')) return '⏰';
    if (lowerName.includes('optimize') || lowerName.includes('sequence')) return '🎯';
    if (lowerName.includes('traffic')) return '🚦';
    return '🔧';
}

function formatToolName(toolName) {
    return toolName
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function parseToolOutput(output) {
    try {
        // Try to parse JSON - handle double-encoded JSON
        let data = output;
        if (typeof output === 'string') {
            try {
                data = JSON.parse(output);
                // Check if it's double-encoded (string inside string)
                if (typeof data === 'string') {
                    data = JSON.parse(data);
                }
            } catch (e) {
                console.log('Failed to parse tool output as JSON:', e);
                return <div style={{ fontSize: '0.8rem', color: '#fca5a5' }}>Failed to parse output</div>;
            }
        }
        
        // Handle null or undefined data
        if (!data || typeof data !== 'object') {
            return <div style={{ fontSize: '0.8rem', color: '#8b92a0' }}>No data available</div>;
        }
        
        // Handle error responses
        if (data.error) {
            return (
                <div style={{ padding: '0.5rem', background: '#2d1f1f', borderRadius: '4px', borderLeft: '3px solid #ef4444' }}>
                    <div style={{ color: '#fca5a5', fontSize: '0.8rem', fontWeight: '600' }}>❌ Error</div>
                    <div style={{ color: '#fca5a5', fontSize: '0.75rem', marginTop: '0.25rem' }}>{data.error}</div>
                </div>
            );
        }
        
        // Format based on tool type
        const entries = [];
        
        // Weather data
        if (data.location && (data.temperature_celsius !== undefined || data.temperature_f !== undefined)) {
            const tempC = data.temperature_celsius !== undefined && data.temperature_celsius !== null
                ? data.temperature_celsius
                : data.temperature_f !== undefined && data.temperature_f !== null
                    ? ((data.temperature_f - 32) * 5) / 9
                    : undefined;
            const tempF = data.temperature_f !== undefined && data.temperature_f !== null
                ? data.temperature_f
                : data.temperature_celsius !== undefined && data.temperature_celsius !== null
                    ? (data.temperature_celsius * 9) / 5 + 32
                    : undefined;
            const conditions = data.current_conditions || data.conditions;
            entries.push(
                <div key="location" style={{ marginBottom: '0.5rem' }}>
                    <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>📍 Location:</span>
                    <span style={{ color: '#e2e8f0', marginLeft: '0.5rem', fontWeight: '600' }}>{data.location}</span>
                </div>,
                <div key="temp" style={{ marginBottom: '0.5rem' }}>
                    <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>🌡️ Temperature:</span>
                    <span style={{ color: '#60a5fa', marginLeft: '0.5rem', fontWeight: '600' }}>
                        {tempC !== undefined ? `${Number(tempC).toFixed(1)}°C` : '—'}
                        {tempF !== undefined ? ` / ${Number(tempF).toFixed(1)}°F` : ''}
                    </span>
                </div>,
                <div key="conditions" style={{ marginBottom: '0.5rem' }}>
                    <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>☁️ Conditions:</span>
                    <span style={{ color: '#86efac', marginLeft: '0.5rem' }}>{conditions || 'Unavailable'}</span>
                </div>
            );
            if (data.humidity_percent !== undefined && data.humidity_percent !== null) {
                entries.push(
                    <div key="humidity" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>💧 Humidity:</span>
                        <span style={{ color: '#93c5fd', marginLeft: '0.5rem' }}>{Math.round(Number(data.humidity_percent))}%</span>
                    </div>
                );
            }
            if ((data.wind_speed_mph !== undefined && data.wind_speed_mph !== null) || (data.wind_speed_kph !== undefined && data.wind_speed_kph !== null)) {
                entries.push(
                    <div key="wind" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>🍃 Wind:</span>
                        <span style={{ color: '#fbbf24', marginLeft: '0.5rem' }}>
                            {data.wind_speed_mph !== undefined && data.wind_speed_mph !== null ? `${Number(data.wind_speed_mph).toFixed(1)} mph` : '—'}
                            {data.wind_speed_kph !== undefined && data.wind_speed_kph !== null ? ` / ${Number(data.wind_speed_kph).toFixed(1)} kph` : ''}
                        </span>
                    </div>
                );
            }
            if (data.precipitation_mm !== undefined && data.precipitation_mm !== null) {
                entries.push(
                    <div key="precip" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>🌧️ Precipitation (1h):</span>
                        <span style={{ color: '#cbd5e0', marginLeft: '0.5rem' }}>{Number(data.precipitation_mm).toFixed(2)} mm</span>
                    </div>
                );
            }
            if (data.alert_level) {
                entries.push(
                    <div key="alert" style={{ marginTop: '0.75rem', padding: '0.5rem', background: data.alert_level === 'normal' ? '#1f2d1f' : '#2d1f1f', borderRadius: '4px', borderLeft: `3px solid ${data.alert_level === 'normal' ? '#10b981' : '#ef4444'}` }}>
                        <div style={{ color: data.alert_level === 'normal' ? '#86efac' : '#fca5a5', fontSize: '0.8rem', fontWeight: '600' }}>
                            {data.alert_level === 'normal' ? '✅ Safe Conditions' : '⚠️ Alert'}
                        </div>
                        {data.delivery_impact && (
                            <div style={{ color: '#cbd5e0', fontSize: '0.75rem', marginTop: '0.25rem' }}>{data.delivery_impact}</div>
                        )}
                    </div>
                );
            }
        }
        
        // Metrics data
        else if (data.distance_km !== undefined || data.estimated_time_hours !== undefined) {
            if (data.distance_km !== undefined) {
                entries.push(
                    <div key="distance" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>📏 Distance:</span>
                        <span style={{ color: '#10b981', marginLeft: '0.5rem', fontWeight: '700', fontSize: '1.1rem' }}>{data.distance_km.toFixed(1)} km</span>
                    </div>
                );
            }
            if (data.estimated_time_hours !== undefined) {
                entries.push(
                    <div key="time" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>⏱️ Duration:</span>
                        <span style={{ color: '#60a5fa', marginLeft: '0.5rem', fontWeight: '700', fontSize: '1.1rem' }}>{data.estimated_time_hours.toFixed(1)}h</span>
                    </div>
                );
            }
            if (data.fuel_consumption_liters) {
                entries.push(
                    <div key="fuel" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>⛽ Fuel:</span>
                        <span style={{ color: '#fbbf24', marginLeft: '0.5rem', fontWeight: '600' }}>{data.fuel_consumption_liters.toFixed(1)}L</span>
                    </div>
                );
            }
        }
        
        // Timing validation data
        else if (data.is_valid !== undefined) {
            entries.push(
                <div key="valid" style={{ marginBottom: '0.75rem', padding: '0.5rem', background: data.is_valid ? '#1f2d1f' : '#2d1f1f', borderRadius: '4px' }}>
                    <span style={{ color: data.is_valid ? '#86efac' : '#fca5a5', fontWeight: '700', fontSize: '0.9rem' }}>
                        {data.is_valid ? '✅ Timing Valid' : '❌ Timing Issues'}
                    </span>
                </div>
            );
            if (data.issues && data.issues.length > 0) {
                entries.push(
                    <div key="issues" style={{ fontSize: '0.8rem', color: '#fca5a5' }}>
                        {data.issues.map((issue, i) => <div key={i}>⚠️ {issue}</div>)}
                    </div>
                );
            }
        }
        
        // Optimization data - handles both old format and new LLM-based format
        else if (data.status === 'no_optimization_needed' || data.status === 'ready_for_optimization') {
            entries.push(
                <div key="status" style={{ marginBottom: '0.75rem', padding: '0.5rem', background: '#1f2d1f', borderRadius: '4px' }}>
                    <span style={{ color: '#86efac', fontWeight: '600', fontSize: '0.85rem' }}>
                        {data.status === 'no_optimization_needed' ? '✅ No Optimization Needed' : '🔄 Ready for Optimization'}
                    </span>
                </div>
            );
            if (data.reason) {
                entries.push(
                    <div key="reason" style={{ fontSize: '0.8rem', color: '#a0aec0', marginBottom: '0.5rem' }}>
                        {data.reason}
                    </div>
                );
            }
            if (data.stop_count !== undefined) {
                entries.push(
                    <div key="count" style={{ fontSize: '0.8rem', color: '#8b92a0' }}>
                        📦 Stops: <span style={{ color: '#cbd5e0', fontWeight: '600' }}>{data.stop_count}</span>
                    </div>
                );
            }
            if (data.total_stops !== undefined) {
                entries.push(
                    <div key="total" style={{ fontSize: '0.8rem', color: '#8b92a0' }}>
                        📦 Total Stops: <span style={{ color: '#cbd5e0', fontWeight: '600' }}>{data.total_stops}</span>
                    </div>
                );
            }
        }
        // Old optimization format (for backward compatibility)
        else if (data.optimized_sequence) {
            entries.push(
                <div key="optimized" style={{ marginBottom: '0.5rem' }}>
                    <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>✨ Optimized:</span>
                    <span style={{ color: data.optimized ? '#86efac' : '#fca5a5', marginLeft: '0.5rem', fontWeight: '600' }}>
                        {data.optimized ? 'Yes' : 'No'}
                    </span>
                </div>,
                <div key="sequence" style={{ marginTop: '0.5rem', padding: '0.5rem', background: '#1f2d1f', borderRadius: '4px', fontSize: '0.8rem' }}>
                    <div style={{ color: '#86efac', fontWeight: '600' }}>
                        {data.optimized_sequence.join(' → ')}
                    </div>
                </div>
            );
            if (data.estimated_improvement) {
                entries.push(
                    <div key="improvement" style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#10b981' }}>
                        💡 {data.estimated_improvement}
                    </div>
                );
            }
        }
        
        // Traffic data
        else if (data.traffic_level) {
            const trafficColor = data.traffic_level === 'light' ? '#10b981' : data.traffic_level === 'moderate' ? '#fbbf24' : '#ef4444';
            entries.push(
                <div key="traffic" style={{ marginBottom: '0.5rem' }}>
                    <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>🚦 Level:</span>
                    <span style={{ color: trafficColor, marginLeft: '0.5rem', fontWeight: '700', textTransform: 'uppercase' }}>
                        {data.traffic_level}
                    </span>
                </div>
            );
            if (data.delay_factor !== undefined) {
                entries.push(
                    <div key="factor" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>⚡ Delay Factor:</span>
                        <span style={{ color: '#fbbf24', marginLeft: '0.5rem', fontWeight: '600' }}>{data.delay_factor.toFixed(2)}x</span>
                    </div>
                );
            }
            if (data.estimated_delay_minutes !== undefined && data.estimated_delay_minutes > 0) {
                entries.push(
                    <div key="delay" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>⏳ Extra Time:</span>
                        <span style={{ color: '#fbbf24', marginLeft: '0.5rem', fontWeight: '600' }}>+{data.estimated_delay_minutes} min</span>
                    </div>
                );
            }
            if (data.recommendation) {
                entries.push(
                    <div key="recommendation" style={{ marginTop: '0.75rem', padding: '0.5rem', background: '#1f2d1f', borderRadius: '4px', borderLeft: '3px solid #10b981', fontSize: '0.75rem', color: '#86efac' }}>
                        💡 {data.recommendation}
                    </div>
                );
            }
        }
        
        // RAG retrieval data
        else if (data.retrieved_documents !== undefined || data.document_count !== undefined) {
            if (data.document_count !== undefined) {
                entries.push(
                    <div key="doc_count" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ color: '#8b92a0', fontSize: '0.8rem' }}>📚 Documents:</span>
                        <span style={{ color: '#10b981', marginLeft: '0.5rem', fontWeight: '700', fontSize: '1.1rem' }}>{data.document_count}</span>
                    </div>
                );
            }
            if (data.query) {
                entries.push(
                    <div key="query" style={{ marginBottom: '0.5rem', fontSize: '0.75rem' }}>
                        <span style={{ color: '#8b92a0' }}>🔍 Query:</span>
                        <div style={{ color: '#93c5fd', marginTop: '0.25rem', fontStyle: 'italic' }}>"{data.query}"</div>
                    </div>
                );
            }
            if (data.status === 'success') {
                entries.push(
                    <div key="status" style={{ marginTop: '0.5rem', padding: '0.5rem', background: '#1f2d1f', borderRadius: '4px', borderLeft: '3px solid #10b981' }}>
                        <span style={{ color: '#86efac', fontSize: '0.75rem', fontWeight: '600' }}>✅ Retrieved Successfully</span>
                    </div>
                );
            }
        }
        
        // Fallback: show first 5-6 key fields in readable format
        if (entries.length === 0) {
            Object.entries(data).slice(0, 6).forEach(([key, value]) => {
                // Skip internal fields, null values, objects, and arrays
                if (typeof value !== 'object' && value !== null && value !== undefined && !key.startsWith('_')) {
                    const displayKey = key.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    // Truncate long strings
                    const displayValue = String(value).length > 100 ? String(value).substring(0, 100) + '...' : String(value);
                    entries.push(
                        <div key={key} style={{ marginBottom: '0.4rem', fontSize: '0.8rem' }}>
                            <span style={{ color: '#8b92a0', fontWeight: '500' }}>{displayKey}:</span>
                            <span style={{ color: '#cbd5e0', marginLeft: '0.5rem' }}>{displayValue}</span>
                        </div>
                    );
                }
            });
        }
        
        // Add data source indicator at the bottom if available
        if (data.data_source) {
            const sourceColor = data.data_source.includes('mapbox') ? '#10b981' : 
                               data.data_source.includes('google') ? '#60a5fa' : '#8b92a0';
            entries.push(
                <div key="data_source" style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #2a3345', fontSize: '0.7rem', color: sourceColor }}>
                    📡 Data: {data.data_source.replace(/_/g, ' ')}
                </div>
            );
        }
        
        return <div>{entries}</div>;
        
    } catch (error) {
        // Fallback for non-JSON output
        return (
            <div style={{ fontSize: '0.8rem', color: '#8b92a0', lineHeight: '1.5' }}>
                {String(output).slice(0, 200)}{output.length > 200 ? '...' : ''}
            </div>
        );
    }
}

/**
 * AgentPanel - Interactive map-based route planning UI
 * 
 * Allows dispatchers to:
 * - Click on map to add delivery stops
 * - Manage stop list (reorder, delete, edit)
 * - Set route constraints and preferences
 * - Send structured RouteRequest to AI validation agent
 */
export function AgentPanel() {
    // Route metadata
    const [routeId, setRouteId] = useState(`RT-${Date.now()}`);
    const [startLocation, setStartLocation] = useState('');
    const [startPoint, setStartPoint] = useState(null); // {lat, lng, location}
    // Set default start time to 8:00 AM today (safe default before shift end)
    const [plannedStartTime, setPlannedStartTime] = useState(() => {
        const today = new Date();
        today.setHours(8, 0, 0, 0);
        return today.toISOString().slice(0, 16);
    });
    const [vehicleId, setVehicleId] = useState('VAN-42');
    const [task, setTask] = useState('validate_and_recommend');

    // Stops management
    const [stops, setStops] = useState([]);
    const stopCounterRef = useRef(1);

    // Constraints
    const [maxDuration, setMaxDuration] = useState(8);
    const [shiftEnd, setShiftEnd] = useState('17:00');
    const [vehicleCapacity, setVehicleCapacity] = useState(1000);
    const [notes, setNotes] = useState('');

    // UI state
    const [pending, setPending] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [showConstraints, setShowConstraints] = useState(false);

    // Map center (San Francisco)
    const [mapCenter] = useState([37.7749, -122.4194]);

    /**
     * Handle map click - first click sets start point, subsequent clicks add delivery stops
     */
    const handleMapClick = useCallback((latlng) => {
        // First click: set start point
        if (!startPoint) {
            const location = `Start at ${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)}`;
            setStartPoint({
                lat: latlng.lat,
                lng: latlng.lng,
                location: location
            });
            setStartLocation(location);
            return;
        }

        // Subsequent clicks: add delivery stops
        const stopId = `S${String(stopCounterRef.current).padStart(3, '0')}`;
        const newStop = {
            stop_id: stopId,
            location: `Stop at ${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)}`,
            lat: latlng.lat,
            lng: latlng.lng,
            sequence_number: stops.length + 1,
            label: `Stop ${stopCounterRef.current}`,
            time_window_start: '',
            time_window_end: '',
            priority: 'normal',
            service_time_minutes: 10, // Default 10 minutes per stop
        };
        setStops(prev => [...prev, newStop]);
        stopCounterRef.current += 1;
    }, [stops.length, startPoint]);

    /**
     * Clear start point to allow reselection
     */
    const clearStartPoint = useCallback(() => {
        setStartPoint(null);
        setStartLocation('');
    }, []);

    /**
     * Delete a stop and renumber remaining stops
     */
    const deleteStop = useCallback((stopId) => {
        setStops(prev => {
            const filtered = prev.filter(s => s.stop_id !== stopId);
            // Renumber sequence
            return filtered.map((stop, index) => ({
                ...stop,
                sequence_number: index + 1,
            }));
        });
    }, []);

    /**
     * Update stop details
     */
    const updateStop = useCallback((stopId, field, value) => {
        setStops(prev => prev.map(stop => 
            stop.stop_id === stopId ? { ...stop, [field]: value } : stop
        ));
    }, []);

    /**
     * Send RouteRequest to AI validation agent
     */
    const sendToAI = async () => {
        if (!startPoint) {
            setError('Please click on the map to set the start point first');
            return;
        }

        if (stops.length === 0) {
            setError('Please add at least one delivery stop by clicking on the map');
            return;
        }

        // Validate start time vs shift end
        const startDateTime = new Date(plannedStartTime);
        const startHour = startDateTime.getHours();
        const startMinute = startDateTime.getMinutes();
        const [shiftEndHour, shiftEndMinute] = shiftEnd.split(':').map(Number);
        
        if (startHour > shiftEndHour || (startHour === shiftEndHour && startMinute > shiftEndMinute)) {
            setError(`Route start time (${startHour.toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}) is after the driver shift end (${shiftEnd}). Please adjust the start time to be before the shift end.`);
            return;
        }

        // Validate that stops have required details
        const incompleteStops = stops.filter(stop => !stop.label || stop.label.trim() === '');
        if (incompleteStops.length > 0) {
            setError(`Please provide names for all stops. ${incompleteStops.length} stop(s) are missing labels.`);
            return;
        }

        setPending(true);
        setError(null);
        setResult(null);

        try {
            // Construct RouteRequest payload
            const routeRequest = {
                route_id: routeId,
                start_location: startLocation,
                start_latitude: startPoint?.lat ?? undefined,
                start_longitude: startPoint?.lng ?? undefined,
                planned_start_time: plannedStartTime + ':00Z', // Add timezone
                vehicle_id: vehicleId || undefined,
                vehicle_type: 'van', // Required for metrics calculation (van/truck/motorcycle)
                stops: stops.map(stop => ({
                    stop_id: stop.stop_id,
                    location: stop.location,
                    sequence_number: stop.sequence_number,
                    time_window_start: stop.time_window_start && stop.time_window_start.trim() !== '' ? stop.time_window_start : undefined,
                    time_window_end: stop.time_window_end && stop.time_window_end.trim() !== '' ? stop.time_window_end : undefined,
                    priority: stop.priority,
                    service_time_minutes: stop.service_time_minutes || 10, // Include service time
                    latitude: typeof stop.lat === 'number' ? stop.lat : undefined,
                    longitude: typeof stop.lng === 'number' ? stop.lng : undefined,
                })),
                constraints: {
                    max_route_duration_hours: maxDuration,
                    driver_shift_end: shiftEnd,
                    vehicle_capacity: vehicleCapacity,
                    notes: notes || undefined,
                },
                task: task,
            };

            console.log('Sending RouteRequest:', routeRequest);
            console.log('Stops state before sending:', stops);

            const response = await fetch('/api/ai/validate-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(routeRequest),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Validation failed');
            }

            const validationResult = await response.json();
            setResult(validationResult);
        } catch (err) {
            setError(err.message);
        } finally {
            setPending(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem', padding: '0.5rem' }}>
            {/* Top Section: Map and Sidebar */}
            <div style={{ display: 'flex', gap: '1.5rem', minHeight: '600px' }}>
            {/* Map Section */}
            <div style={{ flex: '2', minWidth: '0', display: 'flex', flexDirection: 'column' }}>
                <div style={{ marginBottom: '1rem', padding: '1rem', background: 'linear-gradient(135deg, #1a1f2e 0%, #2a2f3a 100%)', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}>
                    <h2 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', fontSize: '1.5rem', fontWeight: '600' }}>
                        <Map size={28} style={{ marginRight: '12px', color: '#60a5fa' }} />
                        Interactive Route Planning
                    </h2>
                    <p style={{ margin: '0', color: '#a0aec0', fontSize: '0.95rem' }}>
                        {!startPoint ? (
                            <span style={{ color: '#10b981', fontWeight: '500' }}>🎯 Click on the map to set your START POINT first</span>
                        ) : (
                            <span>✅ Start point set. Click to add delivery stops.</span>
                        )}
                    </p>
                </div>

                <div style={{ flex: '1', minHeight: '500px', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', border: '2px solid #3a3f4a' }}>
                    <MapContainer
                        center={mapCenter}
                        zoom={13}
                        style={{ height: '100%', width: '100%' }}
                    >
                        <TileLayer
                            attribution='© <a href="https://www.mapbox.com/about/maps/">Mapbox</a>'
                            url="https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiYWhtZWRlbGFnYW15MTMyIiwiYSI6ImNtamt5NHR4ODI2dHYzZ3F4d2JjNDltbmcifQ.PXy1wcZgys6mjn-sV7sMeA"
                        />
                        <MapClickHandler onMapClick={handleMapClick} />
                        
                        {/* Start Point Marker */}
                        {startPoint && (
                            <Marker 
                                key="start-point" 
                                position={[startPoint.lat, startPoint.lng]}
                            >
                                <Popup>
                                    <strong style={{ color: '#10b981' }}>🏁 START POINT</strong>
                                    <br />
                                    <small>{startPoint.location}</small>
                                </Popup>
                            </Marker>
                        )}
                        
                        {/* Delivery Stop Markers */}
                        {stops.map((stop) => (
                            <Marker key={stop.stop_id} position={[stop.lat, stop.lng]}>
                                <Popup>
                                    <strong>#{stop.sequence_number}: {stop.label}</strong>
                                    <br />
                                    <small>{stop.location}</small>
                                </Popup>
                            </Marker>
                        ))}
                    </MapContainer>
                </div>
            </div>

            {/* Sidebar */}
            <div style={{ flex: '1', minWidth: '360px', maxWidth: '420px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                {/* Route Metadata */}
                <div style={{ marginBottom: '1rem', padding: '1.25rem', background: '#1e2330', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)', border: '1px solid #2a3142' }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: '#e2e8f0', borderBottom: '2px solid #3a3f4a', paddingBottom: '0.5rem' }}>📋 Route Details</h3>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                        <label htmlFor="routeId" style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', fontWeight: '500', color: '#cbd5e0' }}>Route ID</label>
                        <input
                            type="text"
                            id="routeId"
                            value={routeId}
                            onChange={(e) => setRouteId(e.target.value)}
                            placeholder="RT-001"
                            style={{ width: '100%', padding: '0.6rem', fontSize: '0.95rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0f1419', color: '#e2e8f0' }}
                        />
                    </div>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                        <label htmlFor="startLocation" style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', fontWeight: '500', color: '#cbd5e0' }}>
                            Start Location
                            {startPoint && (
                                <button
                                    onClick={clearStartPoint}
                                    style={{
                                        marginLeft: '0.5rem',
                                        padding: '0.2rem 0.5rem',
                                        fontSize: '0.75rem',
                                        background: '#ff6b6b',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: 'pointer'
                                    }}
                                    title="Clear and reselect start point"
                                >
                                    Reset
                                </button>
                            )}
                        </label>
                        <input
                            type="text"
                            id="startLocation"
                            value={startLocation}
                            onChange={(e) => setStartLocation(e.target.value)}
                            placeholder={startPoint ? "Click map to set start" : "Click map first, then edit here"}
                            readOnly={!startPoint}
                            style={{ 
                                width: '100%', 
                                padding: '0.6rem', 
                                fontSize: '0.95rem', 
                                borderRadius: '6px', 
                                border: startPoint ? '1px solid #10b981' : '1px solid #3a3f4a', 
                                background: startPoint ? '#0f1419' : '#1a1f2e', 
                                color: startPoint ? '#e2e8f0' : '#6b7280',
                                cursor: startPoint ? 'text' : 'not-allowed'
                            }}
                        />
                    </div>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                        <label htmlFor="plannedStartTime" style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', fontWeight: '500', color: '#cbd5e0' }}>
                            Planned Start Time
                            <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: '#60a5fa', fontWeight: 'normal' }}>
                                (must be before {shiftEnd})
                            </span>
                        </label>
                        <input
                            type="datetime-local"
                            id="plannedStartTime"
                            value={plannedStartTime}
                            onChange={(e) => setPlannedStartTime(e.target.value)}
                            style={{ width: '100%', padding: '0.6rem', fontSize: '0.95rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0f1419', color: '#e2e8f0' }}
                        />
                    </div>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                        <label htmlFor="vehicleId" style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', fontWeight: '500', color: '#cbd5e0' }}>Vehicle ID</label>
                        <input
                            type="text"
                            id="vehicleId"
                            value={vehicleId}
                            onChange={(e) => setVehicleId(e.target.value)}
                            placeholder="VAN-42"
                            style={{ width: '100%', padding: '0.6rem', fontSize: '0.95rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0f1419', color: '#e2e8f0' }}
                        />
                    </div>
                    <div className="form-group" style={{ marginBottom: '0' }}>
                        <label htmlFor="task" style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', fontWeight: '500', color: '#cbd5e0' }}>Task</label>
                        <select
                            id="task"
                            value={task}
                            onChange={(e) => setTask(e.target.value)}
                            style={{ width: '100%', padding: '0.6rem', fontSize: '0.95rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0f1419', color: '#e2e8f0' }}
                        >
                            <option value="validate_route">Validate Route</option>
                            <option value="optimize_route">Optimize Route</option>
                            <option value="validate_and_recommend">Validate & Recommend</option>
                        </select>
                    </div>
                </div>

                {/* Constraints (collapsible) */}
                <div style={{ marginBottom: '1rem', padding: '1.25rem', background: '#1e2330', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)', border: '1px solid #2a3142' }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: '#e2e8f0', borderBottom: '2px solid #3a3f4a', paddingBottom: '0.5rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', userSelect: 'none' }}
                        onClick={() => setShowConstraints(!showConstraints)}>
                        <span style={{ display: 'flex', alignItems: 'center' }}>
                            <Settings size={20} style={{ marginRight: '10px', color: '#60a5fa' }} />
                            ⚙️ Constraints
                        </span>
                        <span style={{ fontSize: '1rem', color: '#60a5fa' }}>{showConstraints ? '▼' : '▶'}</span>
                    </h3>
                    {showConstraints && (
                        <>
                            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                                <label htmlFor="maxDuration">Max Duration (hours)</label>
                                <input
                                    type="number"
                                    id="maxDuration"
                                    value={maxDuration}
                                    onChange={(e) => setMaxDuration(Number(e.target.value))}
                                    min="1"
                                    max="24"
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                                <label htmlFor="shiftEnd">Driver Shift End</label>
                                <input
                                    type="time"
                                    id="shiftEnd"
                                    value={shiftEnd}
                                    onChange={(e) => setShiftEnd(e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                                <label htmlFor="vehicleCapacity">Vehicle Capacity</label>
                                <input
                                    type="number"
                                    id="vehicleCapacity"
                                    value={vehicleCapacity}
                                    onChange={(e) => setVehicleCapacity(Number(e.target.value))}
                                    placeholder="1000"
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                                <label htmlFor="notes">Notes</label>
                                <textarea
                                    id="notes"
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    placeholder="Additional constraints or notes..."
                                    rows="2"
                                />
                            </div>
                        </>
                    )}
                </div>

                {/* Stops List */}
                <div style={{ marginBottom: '1rem', padding: '1.25rem', background: '#1e2330', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)', border: '1px solid #2a3142' }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: '#e2e8f0', borderBottom: '2px solid #3a3f4a', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center' }}>
                        <MapPin size={20} style={{ marginRight: '10px', color: '#10b981' }} />
                        📍 Delivery Stops
                        <span style={{ marginLeft: 'auto', fontSize: '0.9rem', fontWeight: '500', color: '#60a5fa', background: '#1e3a5f', padding: '0.25rem 0.75rem', borderRadius: '12px' }}>{stops.length}</span>
                    </h3>
                    {stops.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '2rem 1rem', background: '#0f1419', borderRadius: '8px', border: '2px dashed #3a3f4a' }}>
                            <Plus size={40} style={{ display: 'block', margin: '0 auto 0.75rem', color: '#4a5568' }} />
                            <p style={{ margin: '0', color: '#718096', fontSize: '0.95rem' }}>Click on the map to add delivery stops</p>
                        </div>
                    ) : (
                        <div style={{ maxHeight: '350px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                            {stops.map((stop, index) => (
                                <div key={stop.stop_id} style={{
                                    padding: '1rem',
                                    marginBottom: '0.75rem',
                                    background: 'linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%)',
                                    borderRadius: '8px',
                                    border: '1px solid #3a3f4a',
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                        <span style={{ fontSize: '1rem', fontWeight: '600', color: '#60a5fa', background: '#1e3a5f', padding: '0.25rem 0.75rem', borderRadius: '6px' }}>#{stop.sequence_number}</span>
                                        <button
                                            onClick={() => deleteStop(stop.stop_id)}
                                            style={{
                                                background: '#2d1f1f',
                                                border: '1px solid #ff6b6b',
                                                borderRadius: '6px',
                                                color: '#ff6b6b',
                                                cursor: 'pointer',
                                                padding: '0.4rem 0.6rem',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.25rem',
                                                fontSize: '0.85rem'
                                            }}
                                            title="Delete stop"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                    <input
                                        type="text"
                                        value={stop.label}
                                        onChange={(e) => updateStop(stop.stop_id, 'label', e.target.value)}
                                        placeholder="Stop name (e.g., Customer A)"
                                        style={{ width: '100%', marginBottom: '0.75rem', fontSize: '0.95rem', padding: '0.6rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0a0e14', color: '#e2e8f0', fontWeight: '500' }}
                                    />
                                    <div style={{ fontSize: '0.85rem', color: '#8b92a0', marginBottom: '0.75rem', padding: '0.5rem', background: '#0a0e14', borderRadius: '4px', borderLeft: '3px solid #4a5568' }}>
                                        📍 {stop.location}
                                    </div>
                                    <div style={{ marginBottom: '0.75rem' }}>
                                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#a0aec0', marginBottom: '0.4rem', fontWeight: '500' }}>⏰ Time Window</label>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                            <input
                                                type="time"
                                                value={stop.time_window_start}
                                                onChange={(e) => updateStop(stop.stop_id, 'time_window_start', e.target.value)}
                                                placeholder="Start"
                                                style={{ padding: '0.5rem', fontSize: '0.85rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0a0e14', color: '#e2e8f0' }}
                                            />
                                            <input
                                                type="time"
                                                value={stop.time_window_end}
                                                onChange={(e) => updateStop(stop.stop_id, 'time_window_end', e.target.value)}
                                                placeholder="End"
                                                style={{ padding: '0.5rem', fontSize: '0.85rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0a0e14', color: '#e2e8f0' }}
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#a0aec0', marginBottom: '0.4rem', fontWeight: '500' }}>🎯 Priority</label>
                                        <select
                                            value={stop.priority}
                                            onChange={(e) => updateStop(stop.stop_id, 'priority', e.target.value)}
                                            style={{ width: '100%', padding: '0.5rem', fontSize: '0.9rem', borderRadius: '6px', border: '1px solid #3a3f4a', background: '#0a0e14', color: '#e2e8f0', fontWeight: '500' }}
                                        >
                                            <option value="low">🔵 Low Priority</option>
                                            <option value="normal">🟢 Normal Priority</option>
                                            <option value="high">🔴 High Priority</option>
                                        </select>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Send Button */}
                <button
                    onClick={sendToAI}
                    disabled={pending || stops.length === 0}
                    style={{
                        width: '100%',
                        padding: '1rem',
                        fontSize: '1.05rem',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.75rem',
                        background: pending || stops.length === 0 ? '#2a2f3a' : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                        color: pending || stops.length === 0 ? '#6b7280' : 'white',
                        border: 'none',
                        borderRadius: '12px',
                        cursor: pending || stops.length === 0 ? 'not-allowed' : 'pointer',
                        boxShadow: pending || stops.length === 0 ? 'none' : '0 4px 12px rgba(59, 130, 246, 0.4)',
                        opacity: pending || stops.length === 0 ? 0.5 : 1
                    }}
                >
                    <Send size={20} />
                    {pending ? '🤖 Validating Route...' : '🚀 Send to AI Route Planner'}
                </button>

                {/* Error Display */}
                {error && (
                    <div className="alert alert-error" style={{ marginTop: '1rem' }}>
                        {error}
                    </div>
                )}
            </div>
            </div>

            {/* Results Section - Below Map */}
            {result && (
                <div style={{ padding: '1.5rem', background: '#1e2330', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', border: '1px solid #2a3142' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', borderBottom: '2px solid #3a3f4a', paddingBottom: '1rem' }}>
                        <h2 style={{ margin: '0', fontSize: '1.5rem', fontWeight: '600', color: '#e2e8f0' }}>
                            📊 Validation Report
                        </h2>
                        <span style={{
                            display: 'inline-block',
                            padding: '0.5rem 1rem',
                            borderRadius: '12px',
                            fontSize: '1rem',
                            fontWeight: 'bold',
                            backgroundColor: result.is_valid ? '#10b981' : '#ef4444',
                            color: 'white'
                        }}>
                            {result.is_valid ? '✓ VALID' : '✗ INVALID'}
                        </span>
                    </div>

                    {/* Summary */}
                    <div style={{ padding: '1rem', background: '#0f1419', borderRadius: '8px', marginBottom: '1.5rem', borderLeft: '4px solid #60a5fa' }}>
                        <p style={{ margin: '0', fontSize: '1rem', lineHeight: '1.6', color: '#e2e8f0' }}>{result.summary}</p>
                    </div>

                    {result.action_plan && result.action_plan.length > 0 && (
                        <div style={{ marginBottom: '1.5rem', padding: '1rem', background: '#132032', borderRadius: '8px', border: '1px solid #2b3b52' }}>
                            <h3 style={{ fontSize: '1.1rem', marginTop: 0, marginBottom: '0.75rem', color: '#93c5fd', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                🗺️ Step-by-Step Plan
                            </h3>
                            <ol style={{ margin: 0, paddingLeft: '1.25rem', color: '#cbd5e0', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                {result.action_plan.map((step, index) => (
                                    <li key={index} style={{ lineHeight: '1.6', background: '#0a0e14', borderRadius: '6px', padding: '0.6rem 0.75rem', borderLeft: '3px solid #60a5fa', listStyle: 'decimal' }}>
                                        <span style={{ color: '#e2e8f0' }}>{step}</span>
                                    </li>
                                ))}
                            </ol>
                        </div>
                    )}

                    {/* Grid Layout for Issues and Recommendations */}
                    <div style={{ display: 'grid', gridTemplateColumns: result.issues?.length > 0 && result.recommendations?.length > 0 ? '1fr 1fr' : '1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                        {/* Issues */}
                        {result.issues && result.issues.length > 0 && (
                            <div style={{ padding: '1rem', background: '#2d1f1f', borderRadius: '8px', border: '1px solid #ff6b6b' }}>
                                <h3 style={{ fontSize: '1.1rem', marginTop: '0', marginBottom: '1rem', color: '#ff6b6b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    ⚠️ Issues
                                </h3>
                                <ul style={{ paddingLeft: '1.5rem', margin: '0', fontSize: '0.95rem', lineHeight: '1.8' }}>
                                    {result.issues.map((issue, i) => (
                                        <li key={i} style={{ marginBottom: '0.5rem', color: '#fca5a5' }}>{issue}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Recommendations */}
                        {result.recommendations && result.recommendations.length > 0 && (
                            <div style={{ padding: '1rem', background: '#1e3a5f', borderRadius: '8px', border: '1px solid #60a5fa' }}>
                                <h3 style={{ fontSize: '1.1rem', marginTop: '0', marginBottom: '1rem', color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    💡 Recommendations
                                </h3>
                                <ul style={{ paddingLeft: '1.5rem', margin: '0', fontSize: '0.95rem', lineHeight: '1.8' }}>
                                    {result.recommendations.map((rec, i) => (
                                        <li key={i} style={{ marginBottom: '0.5rem', color: '#93c5fd' }}>{rec}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>

                    {/* Optimized Order and Metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: result.optimized_stop_order ? '2fr 1fr' : '1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                        {result.optimized_stop_order && (
                            <div style={{ padding: '1rem', background: '#1f2d1f', borderRadius: '8px', border: '1px solid #10b981' }}>
                                <h3 style={{ fontSize: '1.1rem', marginTop: '0', marginBottom: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    🎯 Optimized Stop Order
                                </h3>
                                <div style={{ fontSize: '0.95rem', color: '#86efac', fontWeight: '500', padding: '0.75rem', background: '#0a0e14', borderRadius: '6px' }}>
                                    {result.optimized_stop_order.join(' → ')}
                                </div>
                            </div>
                        )}

                        {(result.estimated_duration_hours || result.estimated_distance_km) && (
                            <div style={{ padding: '1rem', background: '#0f1419', borderRadius: '8px', border: '1px solid #4a5568' }}>
                                <h3 style={{ fontSize: '1.1rem', marginTop: '0', marginBottom: '0.75rem', color: '#a0aec0' }}>📈 Metrics</h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.95rem' }}>
                                    {result.estimated_duration_hours && (
                                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1a1f2e', borderRadius: '4px' }}>
                                            <strong style={{ color: '#cbd5e0' }}>Duration:</strong>
                                            <span style={{ color: '#60a5fa', fontWeight: '600' }}>{result.estimated_duration_hours.toFixed(2)}h</span>
                                        </div>
                                    )}
                                    {result.estimated_distance_km && (
                                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#1a1f2e', borderRadius: '4px' }}>
                                            <strong style={{ color: '#cbd5e0' }}>Distance:</strong>
                                            <span style={{ color: '#10b981', fontWeight: '600' }}>{result.estimated_distance_km.toFixed(1)}km</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Tools Used Section */}
                    {result.tool_calls && result.tool_calls.length > 0 && (
                        <div style={{ padding: '1.5rem', background: 'linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%)', borderRadius: '12px', border: '1px solid #3a3f4a', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }}>
                            <h3 style={{ fontSize: '1.3rem', marginTop: '0', marginBottom: '1.5rem', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: '700', borderBottom: '2px solid #3a3f4a', paddingBottom: '0.75rem' }}>
                                🛠️ AI Tools Used in Analysis
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
                                {result.tool_calls.map((tool, i) => {
                                    const toolName = tool.name || tool.tool || 'Unknown Tool';
                                    const toolIcon = getToolIcon(toolName);
                                    // Handle different output field names and ensure we parse the actual output
                                    let toolOutput = tool.output || tool.output_preview || tool.result || '{}';
                                    const rawOutputString = typeof toolOutput === 'string' ? toolOutput : JSON.stringify(toolOutput, null, 2);
                                    // If output is already an object, use it; otherwise parse it
                                    if (typeof toolOutput === 'string') {
                                        try {
                                            toolOutput = JSON.parse(toolOutput);
                                        } catch (e) {
                                            // Keep as string if parsing fails
                                        }
                                    }
                                    const parsedOutput = parseToolOutput(toolOutput);
                                    const previewText = rawOutputString.length > 300 ? `${rawOutputString.slice(0, 300)}…` : rawOutputString;
                                    
                                    return (
                                        <div key={i} style={{ 
                                            padding: '1.25rem', 
                                            background: 'linear-gradient(135deg, #1e2736 0%, #141820 100%)', 
                                            borderRadius: '10px', 
                                            border: '1px solid #2a3345',
                                            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                            transition: 'all 0.3s ease',
                                            cursor: 'pointer'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.transform = 'translateY(-2px)';
                                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(96, 165, 250, 0.2)';
                                            e.currentTarget.style.borderColor = '#60a5fa';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.transform = 'translateY(0)';
                                            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
                                            e.currentTarget.style.borderColor = '#2a3345';
                                        }}>
                                            {/* Tool Header */}
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', borderBottom: '1px solid #2a3345', paddingBottom: '0.75rem' }}>
                                                <span style={{ fontSize: '1.5rem' }}>{toolIcon}</span>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontSize: '1rem', fontWeight: '700', color: '#60a5fa', marginBottom: '0.25rem' }}>
                                                        {formatToolName(toolName)}
                                                    </div>
                                                    <div style={{ fontSize: '0.75rem', color: '#8b92a0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                                        Analysis Complete
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            {/* Tool Output */}
                                            <div style={{ fontSize: '0.75rem', color: '#8b92a0', marginBottom: '0.75rem', padding: '0.5rem', background: '#0a0e14', borderRadius: '6px', border: '1px solid #2a3345' }}>
                                                <strong style={{ color: '#60a5fa', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Output Preview:</strong>
                                                <div style={{ marginTop: '0.35rem', whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>{previewText || 'No output provided.'}</div>
                                            </div>
                                            <div style={{ fontSize: '0.85rem', color: '#cbd5e0', lineHeight: '1.6' }}>
                                                {parsedOutput}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AgentPanel;
