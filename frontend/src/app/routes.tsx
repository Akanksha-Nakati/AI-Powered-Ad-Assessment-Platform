import { createBrowserRouter } from "react-router-dom";
import { AssessPage } from "../features/assess/AssessPage";
import { BrandsPage } from "../features/brands/BrandsPage";
import { ComparePage } from "../features/compare/ComparePage";
import { AssessmentDetailPage } from "../features/history/AssessmentDetailPage";
import { HistoryPage } from "../features/history/HistoryPage";
import { Layout } from "./Layout";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <AssessPage /> },
      { path: "compare", element: <ComparePage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "history/:id", element: <AssessmentDetailPage /> },
      { path: "brands", element: <BrandsPage /> },
    ],
  },
]);
