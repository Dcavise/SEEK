import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import PropertyDetail from "./pages/property/[id]";
import ImportIndex from "./pages/import/index";
import ImportMapping from "./pages/import/mapping";
import ImportPreview from "./pages/import/preview";
import ImportResults from "./pages/import/results";
import TeamIndex from "./pages/team/index";
import TeamAssignments from "./pages/team/assignments";
import AnalyticsIndex from "./pages/analytics/index";
import AnalyticsPipeline from "./pages/analytics/pipeline";
import SettingsProfile from "./pages/settings/profile";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/property/:id" element={<PropertyDetail />} />
          <Route path="/import" element={<ImportIndex />} />
          <Route path="/import/mapping" element={<ImportMapping />} />
          <Route path="/import/preview" element={<ImportPreview />} />
          <Route path="/import/results" element={<ImportResults />} />
          <Route path="/team" element={<TeamIndex />} />
          <Route path="/team/assignments" element={<TeamAssignments />} />
          <Route path="/analytics" element={<AnalyticsIndex />} />
          <Route path="/analytics/pipeline" element={<AnalyticsPipeline />} />
          <Route path="/settings/profile" element={<SettingsProfile />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
