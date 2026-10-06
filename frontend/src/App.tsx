import { Spin } from "antd";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AppLayout from "./components/AppLayout";
import JobDetailPage from "./pages/JobDetailPage";
import JobsPage from "./pages/JobsPage";
import LoginPage from "./pages/LoginPage";
import WatchesPage from "./pages/WatchesPage";

function RequireAuth() {
  const { user, initializing } = useAuth();
  if (initializing) return <div className="center-state"><Spin size="large" tip="正在确认登录状态" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export default function App() {
  return <BrowserRouter><AuthProvider><Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<RequireAuth />}>
      <Route element={<AppLayout />}>
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        <Route path="/watches" element={<WatchesPage />} />
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/jobs" replace />} />
  </Routes></AuthProvider></BrowserRouter>;
}
