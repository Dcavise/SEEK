import React from 'react';
import { Header } from '@/components/shared/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { BarChart3, TrendingUp, MapPin, Building, Download } from 'lucide-react';

const AnalyticsIndex = () => {
  const marketData = [
    {
      city: 'Austin, TX',
      totalProperties: 247,
      qualified: 89,
      reviewing: 102,
      disqualified: 56,
      qualificationRate: '36%'
    },
    {
      city: 'Denver, CO',
      totalProperties: 186,
      qualified: 67,
      reviewing: 78,
      disqualified: 41,
      qualificationRate: '36%'
    },
    {
      city: 'Seattle, WA',
      totalProperties: 134,
      qualified: 52,
      reviewing: 45,
      disqualified: 37,
      qualificationRate: '39%'
    }
  ];

  const overallStats = marketData.reduce((acc, market) => ({
    totalProperties: acc.totalProperties + market.totalProperties,
    qualified: acc.qualified + market.qualified,
    reviewing: acc.reviewing + market.reviewing,
    disqualified: acc.disqualified + market.disqualified
  }), { totalProperties: 0, qualified: 0, reviewing: 0, disqualified: 0 });

  const overallQualificationRate = Math.round((overallStats.qualified / overallStats.totalProperties) * 100);

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 p-6 max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-foreground mb-2">Market Analytics</h1>
            <p className="text-muted-foreground">
              Property evaluation performance across markets
            </p>
          </div>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        </div>

        {/* Overall Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Building className="h-5 w-5" />
                Total Properties
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{overallStats.totalProperties}</div>
              <p className="text-sm text-muted-foreground">Across all markets</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5 text-qualified" />
                Qualified
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{overallStats.qualified}</div>
              <p className="text-sm text-muted-foreground">{overallQualificationRate}% qualification rate</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <BarChart3 className="h-5 w-5 text-review" />
                In Review
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{overallStats.reviewing}</div>
              <p className="text-sm text-muted-foreground">Pending evaluation</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Building className="h-5 w-5 text-destructive" />
                Disqualified
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{overallStats.disqualified}</div>
              <p className="text-sm text-muted-foreground">Did not meet criteria</p>
            </CardContent>
          </Card>
        </div>

        {/* Market Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Market Performance</CardTitle>
            <CardDescription>
              Property evaluation breakdown by market
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {marketData.map((market, index) => (
                <div key={index} className="p-4 border border-border rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-5 w-5 text-primary" />
                      <h3 className="font-semibold text-foreground">{market.city}</h3>
                      <Badge variant="outline">{market.qualificationRate} qualified</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {market.totalProperties} total properties
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-qualified">{market.qualified}</div>
                      <div className="text-sm text-muted-foreground">Qualified</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-review">{market.reviewing}</div>
                      <div className="text-sm text-muted-foreground">Reviewing</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-destructive">{market.disqualified}</div>
                      <div className="text-sm text-muted-foreground">Disqualified</div>
                    </div>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full flex">
                      <div 
                        className="bg-qualified" 
                        style={{ width: `${(market.qualified / market.totalProperties) * 100}%` }}
                      />
                      <div 
                        className="bg-review" 
                        style={{ width: `${(market.reviewing / market.totalProperties) * 100}%` }}
                      />
                      <div 
                        className="bg-destructive" 
                        style={{ width: `${(market.disqualified / market.totalProperties) * 100}%` }}
                      />
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

export default AnalyticsIndex;