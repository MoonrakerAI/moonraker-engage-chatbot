import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart3, 
  MessageSquare, 
  MapPin, 
  Stethoscope, 
  BookOpen, 
  Settings, 
  Globe,
  User,
  TestTube
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/practice-info', icon: User, label: 'Practice Info' },
    { path: '/locations', icon: MapPin, label: 'Locations' },
    { path: '/services', icon: Stethoscope, label: 'Services & Treatment' },
    { path: '/knowledge-base', icon: BookOpen, label: 'Knowledge Base' },
    { path: '/chatbot-setup', icon: MessageSquare, label: 'Chatbot Setup' },
    { path: '/website-integration', icon: Globe, label: 'Website Integration' },
    { path: '/account-settings', icon: Settings, label: 'Account Settings' },
    { path: '/test-claude', icon: TestTube, label: 'Test Claude' }
  ];

  return (
    <div className="w-64 bg-white shadow-lg border-r border-gray-200 h-full">
      {/* Logo/Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">M</span>
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">Moonraker</h1>
            <p className="text-sm text-gray-600">Engage</p>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">HIPAA-Compliant AI Chatbot</p>
      </div>

      {/* Navigation */}
      <nav className="p-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-gray-100 text-gray-900 font-medium'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`
                }
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Help Section */}
      <div className="absolute bottom-4 left-4 right-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 text-sm mb-1">Need Help?</h4>
          <p className="text-xs text-gray-600 mb-3">
            Check our documentation or contact support.
          </p>
          <button className="flex items-center space-x-2 text-xs text-blue-600 hover:text-blue-700">
            <MessageSquare className="w-3 h-3" />
            <span>Get Support</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;