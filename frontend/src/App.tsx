import { Spin } from "antd";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AppLayout from "./components/AppLayout";
import JobDetailPage from "./pages/JobDetailPage";
import JobsPage from "./pages/JobsPage";
import LoginPage from "./pages/LoginPage";
import WatchesPage from "./pages/WatchesPage";
import WatchEventsPage from "./pages/WatchEventsPage";
import WatchEventDetailPage from "./pages/WatchEventDetailPage";
import ReplayPage from "./pages/ReplayPage";
import CollectionPage from "./pages/CollectionPage";

function RequireAuth() {
  const { user, initializing } = useAuth();
  if (initializing) return <div className="center-state"><Spin size="large" tip="正在确认登录状态" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

function RequireMaintainer() {
  const { user } = useAuth();
  return user?.role === "maintainer" ? <Outlet /> : <Navigate to="/jobs" replace />;
}

export default function App() {
  return <BrowserRouter><AuthProvider><Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<RequireAuth />}>
      <Route element={<AppLayout />}>
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        <Route path="/watches" element={<WatchesPage />} />
        <Route path="/watch-events" element={<WatchEventsPage />} />
        <Route path="/watch-events/:eventId" element={<WatchEventDetailPage />} />
        <Route element={<RequireMaintainer />}>
          <Route path="/maintenance/collection" element={<CollectionPage />} />
          <Route path="/maintenance/replay" element={<ReplayPage />} />
        </Route>
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/jobs" replace />} />
  </Routes></AuthProvider></BrowserRouter>;
}
