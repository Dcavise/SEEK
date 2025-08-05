import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/shared/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ArrowLeft, Clock, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

const AnalyticsPipeline = () => {
  const navigate = useNavigate();

  const pipelineStages = [
    {
      name: 'Unreviewed',
      count: 156,
      percentage: 28,
      icon: Clock,
      color: 'muted-foreground',
      description: 'Properties awaiting initial review'
    },
    {
      name: 'In Review',
      count: 189,
      percentage: 34,
      icon: AlertTriangle,
      color: 'review',
      description: 'Currently being evaluated'
    },
    {
      name: 'Qualified',
      count: 142,
      percentage: 26,
      icon: CheckCircle,
      color: 'qualified',
      description: 'Meet all requirements'
    },
    {
      name: 'Disqualified',
      count: 67,
      percentage: 12,
      icon: XCircle,
      color: 'destructive',
      description: 'Failed to meet criteria'
    }
  ];

  const weeklyTrends = [
    { week: 'Week 1', qualified: 28, disqualified: 12, reviewed: 45 },
    { week: 'Week 2', qualified: 34, disqualified: 8, reviewed: 52 },
    { week: 'Week 3', qualified: 41, disqualified: 15, reviewed: 67 },
    { week: 'Week 4', qualified: 39, disqualified: 11, reviewed: 58 }
  ];

  const totalProperties = pipelineStages.reduce((acc, stage) => acc + stage.count, 0);

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 p-6 max-w-6xl mx-auto">
        <div className="mb-6">
          <Button variant="ghost" onClick={() => navigate('/analytics')} className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Analytics
          </Button>
          <h1 className="text-2xl font-semibold text-foreground mb-2">Property Pipeline</h1>
          <p className="text-muted-foreground">
            Track properties through the evaluation pipeline by status
          </p>
        </div>

        {/* Pipeline Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {pipelineStages.map((stage) => {
            const Icon = stage.icon;
            return (
              <Card key={stage.name}>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Icon className={`h-5 w-5 text-${stage.color}`} />
                    {stage.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-foreground mb-2">{stage.count}</div>
                  <div className="flex items-center gap-2 mb-2">
                    <Progress value={stage.percentage} className="flex-1" />
                    <span className="text-sm text-muted-foreground">{stage.percentage}%</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{stage.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Pipeline Flow */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Pipeline Flow</CardTitle>
            <CardDescription>
              Visual representation of the property evaluation pipeline
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                {pipelineStages.map((stage, index) => (
                  <div key={stage.name} className="flex flex-col items-center flex-1">
                    <div className={`w-12 h-12 rounded-full border-2 border-${stage.color} bg-background flex items-center justify-center mb-2`}>
                      <stage.icon className={`h-6 w-6 text-${stage.color}`} />
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-foreground">{stage.count}</div>
                      <div className="text-sm text-muted-foreground">{stage.name}</div>
                    </div>
                    {index < pipelineStages.length - 1 && (
                      <div className="absolute top-6 left-1/2 w-full h-0.5 bg-border -z-10" 
                           style={{ left: `${((index + 0.5) / pipelineStages.length) * 100}%`, width: `${100 / pipelineStages.length}%` }} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Weekly Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Completion Trends</CardTitle>
            <CardDescription>
              Properties processed per week over the last month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {weeklyTrends.map((week, index) => (
                <div key={index} className="flex items-center justify-between p-4 border border-border rounded-lg">
                  <div className="font-medium text-foreground">{week.week}</div>
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <Badge variant="default" className="bg-qualified">
                        {week.qualified} Qualified
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="destructive">
                        {week.disqualified} Disqualified
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {week.reviewed} total reviewed
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

export default AnalyticsPipeline;