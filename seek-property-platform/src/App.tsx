import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import AnalyticsIndex from "./pages/analytics/index";
import AnalyticsPipeline from "./pages/analytics/pipeline";
import DebugCSVUpload from "./pages/DebugCSVUpload";
import { FOIAEnhancedReviewTest } from "./pages/FOIAEnhancedReviewTest";
import FOIAImportTest from "./pages/FOIAImportTest";
import ImportIndex from "./pages/import/index";
import ImportMapping from "./pages/import/mapping";
import ImportPreview from "./pages/import/preview";
import ImportResults from "./pages/import/results";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import PropertyDetail from "./pages/property/[id]";
import SettingsProfile from "./pages/settings/profile";
import TeamAssignments from "./pages/team/assignments";
import TeamIndex from "./pages/team/index";

import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";

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
          <Route path="/foia-test" element={<FOIAImportTest />} />
          <Route path="/foia-enhanced-review-test" element={<FOIAEnhancedReviewTest />} />
          <Route path="/debug-csv-upload" element={<DebugCSVUpload />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>
);

export default App;
