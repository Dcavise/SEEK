import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/shared/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Users, UserPlus, Calendar, TrendingUp } from 'lucide-react';

const TeamIndex = () => {
  const navigate = useNavigate();

  const teamMembers = [
    {
      id: '1',
      name: 'Sarah Chen',
      role: 'Senior Analyst',
      email: 'sarah.chen@company.com',
      avatar: '',
      activeProperties: 23,
      completedThisWeek: 8,
      status: 'active'
    },
    {
      id: '2',
      name: 'Mike Rodriguez',
      role: 'Property Analyst',
      email: 'mike.rodriguez@company.com',
      avatar: '',
      activeProperties: 18,
      completedThisWeek: 12,
      status: 'active'
    },
    {
      id: '3',
      name: 'Emma Thompson',
      role: 'Junior Analyst',
      email: 'emma.thompson@company.com',
      avatar: '',
      activeProperties: 15,
      completedThisWeek: 6,
      status: 'away'
    }
  ];

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 p-6 max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-foreground mb-2">Team Dashboard</h1>
            <p className="text-muted-foreground">
              Manage your property evaluation team and workload distribution
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => navigate('/team/assignments')}>
              <Calendar className="mr-2 h-4 w-4" />
              View Assignments
            </Button>
            <Button>
              <UserPlus className="mr-2 h-4 w-4" />
              Add Team Member
            </Button>
          </div>
        </div>

        {/* Team Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="h-5 w-5" />
                Team Size
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{teamMembers.length}</div>
              <p className="text-sm text-muted-foreground">Active members</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5" />
                Active Properties
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {teamMembers.reduce((acc, member) => acc + member.activeProperties, 0)}
              </div>
              <p className="text-sm text-muted-foreground">Currently assigned</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Calendar className="h-5 w-5" />
                This Week
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {teamMembers.reduce((acc, member) => acc + member.completedThisWeek, 0)}
              </div>
              <p className="text-sm text-muted-foreground">Properties completed</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5" />
                Avg. Completion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {Math.round(teamMembers.reduce((acc, member) => acc + member.completedThisWeek, 0) / teamMembers.length)}
              </div>
              <p className="text-sm text-muted-foreground">Per person this week</p>
            </CardContent>
          </Card>
        </div>

        {/* Team Members */}
        <Card>
          <CardHeader>
            <CardTitle>Team Members</CardTitle>
            <CardDescription>
              View and manage your property evaluation team
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {teamMembers.map((member) => (
                <div key={member.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-4">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={member.avatar} />
                      <AvatarFallback>{getInitials(member.name)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-foreground">{member.name}</h3>
                        <Badge variant={member.status === 'active' ? 'default' : 'secondary'}>
                          {member.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{member.role}</p>
                      <p className="text-sm text-muted-foreground">{member.email}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-foreground">
                      {member.activeProperties} active properties
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {member.completedThisWeek} completed this week
                    </div>
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

export default TeamIndex;