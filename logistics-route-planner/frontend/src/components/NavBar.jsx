import React, { useState } from 'react';
import { Bot, MapPin, Search, History, Package, Truck, MessageSquare } from 'lucide-react';
import './NavBar.css';

const TABS = [
  { key: 'agent', label: 'AI Agent', icon: Bot },
  { key: 'chatbot', label: 'AI Chat', icon: MessageSquare },
  { key: 'planner', label: 'Planner', icon: MapPin },
  { key: 'search', label: 'Search Documents', icon: Search },
  { key: 'history', label: 'Recent Runs', icon: History },
  { key: 'echo', label: 'Echo Test', icon: Package },
];

export default function NavBar({ activeTab, onTabChange }) {
  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <h2><Truck size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Route Planner</h2>
      </div>
      <ul className="sidebar-tabs">
        {TABS.map(tab => {
          const IconComponent = tab.icon;
          return (
            <li
              key={tab.key}
              className={activeTab === tab.key ? 'active' : ''}
              onClick={() => onTabChange(tab.key)}
            >
              <span className="tab-icon"><IconComponent size={20} /></span>
              <span className="tab-label">{tab.label}</span>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

