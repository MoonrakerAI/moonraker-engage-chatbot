import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Palette, 
  MessageSquare, 
  Settings, 
  Calendar,
  Upload,
  Eye
} from 'lucide-react';

const ChatbotSetup: React.FC = () => {
  const [branding, setBranding] = useState({
    botName: 'Retreat Bot',
    primaryColor: '#ac7782',
    secondaryColor: '#d3d6de',
    titleFont: 'Inter',
    bodyFont: 'Inter',
    logoUrl: null,
    welcomeMessage: "Hi! I'm here to help you with scheduling and answering questions about our therapy services. How can I assist you today?"
  });

  const [instructions, setInstructions] = useState({
    whatBotShouldSay: "Be warm, professional, and helpful. Focus on scheduling appointments and providing basic practice information.",
    whatBotShouldNeverSay: "Never provide therapy advice, diagnose conditions, or discuss specific treatment details.",
    emergencyInstructions: "For mental health emergencies, direct users to call 988 (Suicide & Crisis Lifeline) or 911.",
    maxMessages: 20
  });

  const [appointmentConfig, setAppointmentConfig] = useState({
    enabled: true,
    googleCalendarId: 'your-calendar@gmail.com',
    startTime: '09:00',
    endTime: '17:00',
    availableDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    appointmentTypes: ['Initial Consultation', 'Individual Therapy', 'Couples Therapy']
  });

  const days = [
    { id: 'monday', label: 'Monday' },
    { id: 'tuesday', label: 'Tuesday' },
    { id: 'wednesday', label: 'Wednesday' },
    { id: 'thursday', label: 'Thursday' },
    { id: 'friday', label: 'Friday' },
    { id: 'saturday', label: 'Saturday' },
    { id: 'sunday', label: 'Sunday' }
  ];

  const fonts = ['Inter', 'Arial', 'Georgia', 'Times New Roman', 'Helvetica'];

  const handleDayToggle = (dayId: string, checked: boolean) => {
    setAppointmentConfig(prev => ({
      ...prev,
      availableDays: checked 
        ? [...prev.availableDays, dayId]
        : prev.availableDays.filter(day => day !== dayId)
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Chatbot Setup</h1>
            <p className="text-gray-600 mt-1">Customize your chatbot's appearance, behavior, messaging, and appointment booking to match your practice brand.</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <Tabs defaultValue="branding" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="branding">Branding & Preview</TabsTrigger>
            <TabsTrigger value="instructions">Bot Instructions</TabsTrigger>
            <TabsTrigger value="settings">Bot Settings</TabsTrigger>
            <TabsTrigger value="booking">Appointment Booking</TabsTrigger>
          </TabsList>

          {/* Branding & Preview Tab */}
          <TabsContent value="branding" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Branding Configuration */}
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Palette className="w-5 h-5" />
                      <span>Branding & Colors</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Bot Name */}
                    <div className="space-y-2">
                      <Label htmlFor="botName">Bot Name</Label>
                      <Input
                        id="botName"
                        value={branding.botName}
                        onChange={(e) => setBranding(prev => ({ ...prev, botName: e.target.value }))}
                        placeholder="Retreat Bot"
                      />
                      <p className="text-sm text-gray-500">This will appear as the title in the chat header.</p>
                    </div>

                    {/* Colors */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="primaryColor">Primary Color</Label>
                        <div className="flex items-center space-x-2">
                          <Input
                            id="primaryColor"
                            type="color"
                            value={branding.primaryColor}
                            onChange={(e) => setBranding(prev => ({ ...prev, primaryColor: e.target.value }))}
                            className="w-16 h-10 p-1 border rounded"
                          />
                          <Input
                            value={branding.primaryColor}
                            onChange={(e) => setBranding(prev => ({ ...prev, primaryColor: e.target.value }))}
                            placeholder="#ac7782"
                          />
                        </div>
                        <p className="text-sm text-gray-500">Used for the chat header and user messages. Text color adjusts automatically for contrast.</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="secondaryColor">Secondary Color</Label>
                        <div className="flex items-center space-x-2">
                          <Input
                            id="secondaryColor"
                            type="color"
                            value={branding.secondaryColor}
                            onChange={(e) => setBranding(prev => ({ ...prev, secondaryColor: e.target.value }))}
                            className="w-16 h-10 p-1 border rounded"
                          />
                          <Input
                            value={branding.secondaryColor}
                            onChange={(e) => setBranding(prev => ({ ...prev, secondaryColor: e.target.value }))}
                            placeholder="#d3d6de"
                          />
                        </div>
                        <p className="text-sm text-gray-500">Used for bot messages and backgrounds. Text color adjusts automatically for contrast.</p>
                      </div>
                    </div>

                    {/* Fonts */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="titleFont">Title Font</Label>
                        <Select
                          value={branding.titleFont}
                          onValueChange={(value) => setBranding(prev => ({ ...prev, titleFont: value }))}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {fonts.map(font => (
                              <SelectItem key={font} value={font}>{font}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-sm text-gray-500">Used for the chatbot header and titles.</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="bodyFont">Body Font</Label>
                        <Select
                          value={branding.bodyFont}
                          onValueChange={(value) => setBranding(prev => ({ ...prev, bodyFont: value }))}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {fonts.map(font => (
                              <SelectItem key={font} value={font}>{font}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-sm text-gray-500">Used for messages and other text content.</p>
                      </div>
                    </div>

                    {/* Practice Logo */}
                    <div className="space-y-2">
                      <Label>Practice Logo</Label>
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 mb-2">Logo uploaded</p>
                        <p className="text-xs text-gray-500">Click the X to remove</p>
                        <Button variant="outline" size="sm" className="mt-2">
                          Upload New Logo
                        </Button>
                      </div>
                      <p className="text-sm text-gray-500">Upload your practice logo to appear in the chat header. Recommended size: 200x60px, max 2MB.</p>
                    </div>

                    {/* Welcome Message */}
                    <div className="space-y-2">
                      <Label htmlFor="welcomeMessage">Welcome Message</Label>
                      <Textarea
                        id="welcomeMessage"
                        value={branding.welcomeMessage}
                        onChange={(e) => setBranding(prev => ({ ...prev, welcomeMessage: e.target.value }))}
                        rows={3}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Live Preview */}
              <div>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Eye className="w-5 h-5" />
                      <span>Live Preview</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Chat Preview */}
                    <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
                      {/* Chat Header */}
                      <div 
                        className="p-4 text-white"
                        style={{ backgroundColor: branding.primaryColor }}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                            <MessageSquare className="w-4 h-4" />
                          </div>
                          <span className="font-medium" style={{ fontFamily: branding.titleFont }}>
                            {branding.botName}
                          </span>
                        </div>
                      </div>

                      {/* Chat Messages */}
                      <div className="p-4 space-y-3">
                        <div className="flex justify-start">
                          <div 
                            className="max-w-xs p-3 rounded-lg text-sm"
                            style={{ 
                              backgroundColor: branding.secondaryColor,
                              fontFamily: branding.bodyFont 
                            }}
                          >
                            {branding.welcomeMessage}
                          </div>
                        </div>
                      </div>

                      {/* Input Area */}
                      <div className="p-4 border-t bg-gray-50">
                        <div className="flex items-center space-x-2">
                          <Input 
                            placeholder="Type your message..." 
                            className="flex-1"
                            style={{ fontFamily: branding.bodyFont }}
                          />
                          <Button size="sm">Send</Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Bot Instructions Tab */}
          <TabsContent value="instructions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="w-5 h-5" />
                  <span>Bot Instructions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="shouldSay">What the bot should say</Label>
                  <Textarea
                    id="shouldSay"
                    value={instructions.whatBotShouldSay}
                    onChange={(e) => setInstructions(prev => ({ ...prev, whatBotShouldSay: e.target.value }))}
                    rows={4}
                    placeholder="Be warm, professional, and helpful..."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="shouldNeverSay">What the bot should never say</Label>
                  <Textarea
                    id="shouldNeverSay"
                    value={instructions.whatBotShouldNeverSay}
                    onChange={(e) => setInstructions(prev => ({ ...prev, whatBotShouldNeverSay: e.target.value }))}
                    rows={4}
                    placeholder="Never provide therapy advice..."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="emergency">Emergency/Crisis Instructions</Label>
                  <Textarea
                    id="emergency"
                    value={instructions.emergencyInstructions}
                    onChange={(e) => setInstructions(prev => ({ ...prev, emergencyInstructions: e.target.value }))}
                    rows={3}
                    placeholder="For mental health emergencies..."
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bot Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>Bot Settings</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="maxMessages">Maximum messages per conversation</Label>
                  <Input
                    id="maxMessages"
                    type="number"
                    value={instructions.maxMessages}
                    onChange={(e) => setInstructions(prev => ({ ...prev, maxMessages: parseInt(e.target.value) }))}
                    min={1}
                    max={100}
                  />
                  <p className="text-sm text-gray-500">Limit the number of messages in a single conversation to prevent endless loops.</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Appointment Booking Tab */}
          <TabsContent value="booking" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5" />
                  <span>Appointment Booking</span>
                </CardTitle>
                <p className="text-sm text-gray-600">Configure how your chatbot handles appointment booking through Google Calendar integration. This allows clients to book appointments directly through the chat interface.</p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Enable Booking */}
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="enableBooking">Enable Appointment Booking</Label>
                    <p className="text-sm text-gray-500">Allow clients to book appointments directly through the chatbot</p>
                  </div>
                  <Switch
                    id="enableBooking"
                    checked={appointmentConfig.enabled}
                    onCheckedChange={(checked) => setAppointmentConfig(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>

                {appointmentConfig.enabled && (
                  <>
                    {/* Google Calendar Integration */}
                    <div className="space-y-4">
                      <h3 className="font-medium flex items-center space-x-2">
                        <Settings className="w-4 h-4" />
                        <span>Google Calendar Integration</span>
                      </h3>
                      
                      <div className="space-y-2">
                        <Label htmlFor="calendarId">Google Calendar ID</Label>
                        <Input
                          id="calendarId"
                          value={appointmentConfig.googleCalendarId}
                          onChange={(e) => setAppointmentConfig(prev => ({ ...prev, googleCalendarId: e.target.value }))}
                          placeholder="your-calendar@gmail.com"
                        />
                        <p className="text-sm text-gray-500">
                          Your Google Calendar ID. Usually your Gmail address or a specific calendar ID. 
                          <a href="#" className="text-blue-600 hover:underline ml-1">How to find your Calendar ID</a>
                        </p>
                      </div>
                    </div>

                    {/* Booking Hours */}
                    <div className="space-y-4">
                      <h3 className="font-medium flex items-center space-x-2">
                        <Clock className="w-4 h-4" />
                        <span>Booking Hours & Availability</span>
                      </h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="startTime">Start Time</Label>
                          <Input
                            id="startTime"
                            type="time"
                            value={appointmentConfig.startTime}
                            onChange={(e) => setAppointmentConfig(prev => ({ ...prev, startTime: e.target.value }))}
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="endTime">End Time</Label>
                          <Input
                            id="endTime"
                            type="time"
                            value={appointmentConfig.endTime}
                            onChange={(e) => setAppointmentConfig(prev => ({ ...prev, endTime: e.target.value }))}
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Available Days</Label>
                        <p className="text-sm text-gray-500">Click days to toggle availability. Selected days will accept bookings.</p>
                        <div className="flex flex-wrap gap-2">
                          {days.map(day => (
                            <Button
                              key={day.id}
                              variant={appointmentConfig.availableDays.includes(day.id) ? "default" : "outline"}
                              size="sm"
                              onClick={() => handleDayToggle(day.id, !appointmentConfig.availableDays.includes(day.id))}
                            >
                              {day.label}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save Button */}
        <div className="flex justify-end pt-6">
          <Button size="lg">
            Save Configuration
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatbotSetup;