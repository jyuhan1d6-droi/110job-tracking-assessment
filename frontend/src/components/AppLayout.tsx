import { Button, Layout, Space, Tag, Typography } from "antd";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const { Header, Content } = Layout;
const { Text } = Typography;

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function signOut() {
    await logout();
    navigate("/login", { replace: true });
  }

  return <Layout className="app-shell">
    <Header className="app-header">
      <Space size="large"><Link className="brand" to="/jobs">岗位搜索与变更追踪</Link><Link className="header-link" to="/jobs">岗位</Link><Link className="header-link" to="/watches">我的关注</Link><Link className="header-link" to="/watch-events">关注动态</Link>{user?.role === "maintainer" && <><Link className="header-link" to="/maintenance/collection">数据采集</Link><Link className="header-link" to="/maintenance/replay">本地回放</Link></>}</Space>
      <Space>
        <Tag color={user?.role === "maintainer" ? "gold" : "green"}>{user?.role === "maintainer" ? "数据维护账号" : "求职者"}</Tag>
        <Text className="header-user">{user?.display_name}</Text>
        <Button size="small" onClick={signOut}>退出</Button>
      </Space>
    </Header>
    <Content className="page-content"><Outlet /></Content>
  </Layout>;
}
