import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { 
  MessageSquare, 
  Calendar, 
  TrendingUp, 
  Clock 
} from 'lucide-react';

const Analytics: React.FC = () => {
  const [stats] = useState({
    totalConversations: 152,
    conversationsChange: '+12% from last week',
    appointmentsBooked: 24,
    appointmentsChange: '+8% from last week',
    conversionRate: 15.8,
    conversionChange: '+3% from last week',
    avgResponseTime: 2.1,
    responseTimeChange: '-0.3s from last week'
  });

  // Weekly activity data (matching the screenshot)
  const weeklyData = [
    { name: 'Mon', conversations: 12, appointments: 3 },
    { name: 'Tue', conversations: 8, appointments: 2 },
    { name: 'Wed', conversations: 22, appointments: 5 },
    { name: 'Thu', conversations: 18, appointments: 4 },
    { name: 'Fri', conversations: 15, appointments: 3 },
    { name: 'Sat', conversations: 8, appointments: 2 },
    { name: 'Sun', conversations: 7, appointments: 2 }
  ];

  // Conversation topics data (matching the pie chart)
  const topicsData = [
    { name: 'Appointment Scheduling', value: 35, color: '#3b82f6' },
    { name: 'Service Information', value: 25, color: '#10b981' },
    { name: 'Insurance Questions', value: 20, color: '#f59e0b' },
    { name: 'Location & Hours', value: 12, color: '#8b5cf6' },
    { name: 'Pricing', value: 8, color: '#ec4899' }
  ];

  // Response time data
  const responseTimeData = [
    { month: 'Jan', time: 3.2 },
    { month: 'Feb', time: 2.8 },
    { month: 'Mar', time: 2.5 },
    { month: 'Apr', time: 2.1 },
    { month: 'May', time: 2.3 },
    { month: 'Jun', time: 2.0 }
  ];

  const getChangeColor = (change: string) => {
    if (change.includes('+')) return 'text-green-600';
    if (change.includes('-') && change.includes('from last week')) return 'text-red-600';
    if (change.includes('-') && change.includes('s from')) return 'text-green-600';
    return 'text-gray-600';
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.dataKey === 'conversations' ? 'Conversations' : 'Appointments'}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const PieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{payload[0].name}</p>
          <p style={{ color: payload[0].payload.color }}>
            {payload[0].value}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
            <p className="text-gray-600 mt-1">Monitor chatbot performance, client interactions, and appointment conversions.</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Conversations</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.totalConversations}</p>
                  <p className={`text-sm ${getChangeColor(stats.conversationsChange)}`}>
                    {stats.conversationsChange}
                  </p>
                </div>
                <MessageSquare className="w-8 h-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Appointments Booked</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.appointmentsBooked}</p>
                  <p className={`text-sm ${getChangeColor(stats.appointmentsChange)}`}>
                    {stats.appointmentsChange}
                  </p>
                </div>
                <Calendar className="w-8 h-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.conversionRate}%</p>
                  <p className={`text-sm ${getChangeColor(stats.conversionChange)}`}>
                    {stats.conversionChange}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.avgResponseTime}s</p>
                  <p className={`text-sm ${getChangeColor(stats.responseTimeChange)}`}>
                    {stats.responseTimeChange}
                  </p>
                </div>
                <Clock className="w-8 h-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Weekly Activity Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Weekly Activity</CardTitle>
              <p className="text-sm text-gray-600">Conversations and appointments over the last week.</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="conversations" fill="#3b82f6" name="Conversations" />
                  <Bar dataKey="appointments" fill="#10b981" name="Appointments" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top Conversation Topics */}
          <Card>
            <CardHeader>
              <CardTitle>Top Conversation Topics</CardTitle>
              <p className="text-sm text-gray-600">Most common topics discussed with the chatbot.</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={topicsData}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {topicsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<PieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              
              {/* Legend */}
              <div className="mt-4 space-y-2">
                {topicsData.map((topic, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: topic.color }}
                      ></div>
                      <span className="text-sm text-gray-700">{topic.name}</span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{topic.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Average Response Time Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Average Response Time</CardTitle>
            <p className="text-sm text-gray-600">Chatbot's average response time over the past months.</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={responseTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [`${value}s`, 'Response Time']}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="time" 
                  stroke="#8b5cf6" 
                  strokeWidth={3}
                  dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;