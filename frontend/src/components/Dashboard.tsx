import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  MessageSquare, 
  Calendar, 
  TrendingUp, 
  Clock,
  Settings,
  User,
  CheckCircle,
  Circle
} from 'lucide-react';

interface DashboardStats {
  totalConversations: number;
  conversationsChange: string;
  appointmentsBooked: number;
  appointmentsChange: string;
  conversionRate: number;
  conversionChange: string;
  avgResponseTime: number;
  responseTimeChange: string;
}

interface RecentConversation {
  initial: string;
  name: string;
  preview: string;
  status: string;
  timeAgo: string;
}

interface ChatbotStatus {
  status: string;
  model: string;
  knowledgeBase: string;
  lastUpdated: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalConversations: 152,
    conversationsChange: '+12% from last week',
    appointmentsBooked: 24,
    appointmentsChange: '+8% from last week',
    conversionRate: 15.8,
    conversionChange: '+3% from last week',
    avgResponseTime: 2.1,
    responseTimeChange: '-0.3s from last week'
  });

  const [recentConversations] = useState<RecentConversation[]>([
    {
      initial: 'S',
      name: 'Sarah Johnson',
      preview: "I'd like to schedule an appointment for next week",
      status: 'Completed',
      timeAgo: '10 min ago'
    },
    {
      initial: 'M',
      name: 'Michael Chen',
      preview: 'Do you accept insurance for therapy sessions?',
      status: 'Ongoing',
      timeAgo: '25 min ago'
    },
    {
      initial: 'E',
      name: 'Emma Wilson',
      preview: 'What are your hours of operation?',
      status: 'Completed',
      timeAgo: '1 hour ago'
    },
    {
      initial: 'J',
      name: 'James Rodriguez',
      preview: 'I need information about couples therapy',
      status: 'Completed',
      timeAgo: '2 hours ago'
    }
  ]);

  const [chatbotStatus] = useState<ChatbotStatus>({
    status: 'Active',
    model: 'Claude 3.5 Sonnet',
    knowledgeBase: '12 documents',
    lastUpdated: '2 days ago'
  });

  const getChangeColor = (change: string) => {
    if (change.includes('+')) return 'text-green-600';
    if (change.includes('-') && change.includes('from last week')) return 'text-red-600';
    if (change.includes('-') && change.includes('s from')) return 'text-green-600'; // Response time improvement
    return 'text-gray-600';
  };

  const getStatusIcon = (status: string) => {
    return status === 'Completed' ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : (
      <Circle className="w-4 h-4 text-blue-500" />
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Overview of your chatbot performance and recent activity.</p>
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

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Conversations */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Recent Conversations</CardTitle>
                <p className="text-sm text-gray-600">Latest interactions with your chatbot</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentConversations.map((conversation, index) => (
                    <div key={index} className="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition-colors">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="font-medium text-gray-700">{conversation.initial}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <p className="font-medium text-gray-900">{conversation.name}</p>
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(conversation.status)}
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              conversation.status === 'Completed' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {conversation.status}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 truncate">{conversation.preview}</p>
                      </div>
                      <span className="text-xs text-gray-500">{conversation.timeAgo}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Chatbot Status */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Chatbot Status</CardTitle>
                <p className="text-sm text-gray-600">Current configuration and status</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Status</span>
                    <Badge variant="default" className="bg-green-100 text-green-800">
                      {chatbotStatus.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Model</span>
                    <span className="text-sm text-gray-900">{chatbotStatus.model}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Knowledge Base</span>
                    <span className="text-sm text-gray-900">{chatbotStatus.knowledgeBase}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Last Updated</span>
                    <span className="text-sm text-gray-900">{chatbotStatus.lastUpdated}</span>
                  </div>
                  <Button className="w-full mt-4" variant="outline">
                    <Settings className="w-4 h-4 mr-2" />
                    Configure Chatbot
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;