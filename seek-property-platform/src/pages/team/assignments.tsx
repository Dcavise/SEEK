import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/shared/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Calendar, MapPin, User } from 'lucide-react';

const TeamAssignments = () => {
  const navigate = useNavigate();
  const [selectedMember, setSelectedMember] = useState<string>('all');

  const teamMembers = [
    { id: '1', name: 'Sarah Chen', role: 'Senior Analyst' },
    { id: '2', name: 'Mike Rodriguez', role: 'Property Analyst' },
    { id: '3', name: 'Emma Thompson', role: 'Junior Analyst' }
  ];

  const assignments = [
    {
      id: '1',
      property: '123 Main St, Austin, TX',
      assignee: 'Sarah Chen',
      assigneeId: '1',
      status: 'reviewing',
      dueDate: '2024-01-20',
      priority: 'high'
    },
    {
      id: '2',
      property: '456 Oak Ave, Austin, TX',
      assignee: 'Mike Rodriguez',
      assigneeId: '2',
      status: 'qualified',
      dueDate: '2024-01-18',
      priority: 'medium'
    },
    {
      id: '3',
      property: '789 Pine St, Austin, TX',
      assignee: 'Emma Thompson',
      assigneeId: '3',
      status: 'unreviewed',
      dueDate: '2024-01-22',
      priority: 'low'
    }
  ];

  const filteredAssignments = selectedMember === 'all' 
    ? assignments 
    : assignments.filter(a => a.assigneeId === selectedMember);

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'qualified': return 'default';
      case 'reviewing': return 'secondary';
      case 'unreviewed': return 'outline';
      default: return 'outline';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 p-6 max-w-6xl mx-auto">
        <div className="mb-6">
          <Button variant="ghost" onClick={() => navigate('/team')} className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Team
          </Button>
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">Property Assignments</h1>
              <p className="text-muted-foreground">
                Track property assignments and deadlines by team member
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Select value={selectedMember} onValueChange={setSelectedMember}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by member" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Members</SelectItem>
                  {teamMembers.map((member) => (
                    <SelectItem key={member.id} value={member.id}>
                      {member.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button>
                <User className="mr-2 h-4 w-4" />
                Bulk Assign
              </Button>
            </div>
          </div>
        </div>

        {/* Assignment Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Total Assignments</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{filteredAssignments.length}</div>
              <p className="text-sm text-muted-foreground">
                {selectedMember === 'all' ? 'Across all members' : 'For selected member'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Due This Week</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {filteredAssignments.filter(a => new Date(a.dueDate) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)).length}
              </div>
              <p className="text-sm text-muted-foreground">Require attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">High Priority</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {filteredAssignments.filter(a => a.priority === 'high').length}
              </div>
              <p className="text-sm text-muted-foreground">Urgent assignments</p>
            </CardContent>
          </Card>
        </div>

        {/* Assignments List */}
        <Card>
          <CardHeader>
            <CardTitle>Current Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredAssignments.map((assignment) => (
                <div key={assignment.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-4">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>{getInitials(assignment.assignee)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-foreground">{assignment.property}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <User className="h-3 w-3" />
                        <span>{assignment.assignee}</span>
                        <Calendar className="h-3 w-3 ml-2" />
                        <span>Due {assignment.dueDate}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={getPriorityColor(assignment.priority)}>
                      {assignment.priority} priority
                    </Badge>
                    <Badge variant={getStatusColor(assignment.status)}>
                      {assignment.status}
                    </Badge>
                    <Button variant="outline" size="sm">
                      Reassign
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TeamAssignments;