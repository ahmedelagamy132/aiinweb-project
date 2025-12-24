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
                planned_start_time: plannedStartTime + ':00Z', // Add timezone
                vehicle_id: vehicleId || undefined,
                stops: stops.map(stop => ({
                    stop_id: stop.stop_id,
                    location: stop.location,
                    sequence_number: stop.sequence_number,
                    time_window_start: stop.time_window_start && stop.time_window_start.trim() !== '' ? stop.time_window_start : undefined,
                    time_window_end: stop.time_window_end && stop.time_window_end.trim() !== '' ? stop.time_window_end : undefined,
                    priority: stop.priority,
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
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
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
                        <div style={{ padding: '1rem', background: '#0f1419', borderRadius: '8px', border: '1px solid #4a5568' }}>
                            <h3 style={{ fontSize: '1.1rem', marginTop: '0', marginBottom: '1rem', color: '#a0aec0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                🔧 Tools Used in Analysis
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '0.75rem' }}>
                                {result.tool_calls.map((tool, i) => (
                                    <div key={i} style={{ padding: '0.75rem', background: '#1a1f2e', borderRadius: '6px', border: '1px solid #2a3142' }}>
                                        <div style={{ fontSize: '0.9rem', fontWeight: '600', color: '#60a5fa', marginBottom: '0.25rem' }}>
                                            {tool.tool.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: '#8b92a0' }}>
                                            {tool.output_preview}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AgentPanel;
