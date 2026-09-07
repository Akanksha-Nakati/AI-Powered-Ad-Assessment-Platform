import { createBrowserRouter } from "react-router-dom";
import { AssessPage } from "../features/assess/AssessPage";
import { BrandsPage } from "../features/brands/BrandsPage";
import { ComparePage } from "../features/compare/ComparePage";
import { AssessmentDetailPage } from "../features/history/AssessmentDetailPage";
import { HistoryPage } from "../features/history/HistoryPage";
import { LandingPage } from "../features/marketing/LandingPage";
import { DataSourcesPage } from "../features/performance/DataSourcesPage";
import { AppLayout } from "./AppLayout";
import { MarketingLayout } from "./MarketingLayout";
import { NotFoundPage } from "./NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MarketingLayout />,
    children: [{ index: true, element: <LandingPage /> }],
  },
  {
    path: "/app",
    element: <AppLayout />,
    children: [
      { index: true, element: <AssessPage /> },
      { path: "compare", element: <ComparePage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "history/:id", element: <AssessmentDetailPage /> },
      { path: "brands", element: <BrandsPage /> },
      { path: "performance", element: <DataSourcesPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
