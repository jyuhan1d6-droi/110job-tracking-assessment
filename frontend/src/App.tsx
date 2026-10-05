import { useEffect, useState } from "react";
import axios from "axios";
import { Alert, Button, Card, Form, Input, Layout, Space, Spin, Tag, Typography } from "antd";

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

type CurrentUser = { id: string; username: string; display_name: string; role: "job_seeker" | "maintainer" };
type LoginValues = { username: string; password: string };

export default function App() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    axios.get<CurrentUser>("/api/auth/me")
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setInitializing(false));
  }, []);

  async function login(values: LoginValues) {
    setSubmitting(true);
    setError("");
    try {
      const { data } = await axios.post<CurrentUser>("/api/auth/login", values);
      setUser(data);
    } catch (requestError) {
      setError(axios.isAxiosError(requestError) ? requestError.response?.data?.detail ?? "登录服务暂时不可用" : "登录服务暂时不可用");
    } finally {
      setSubmitting(false);
    }
  }

  async function logout() {
    try { await axios.post("/api/auth/logout"); } finally { setUser(null); }
  }

  if (initializing) return <div className="center-state"><Spin size="large" tip="正在确认登录状态" /></div>;

  if (!user) {
    return (
      <Layout className="app-shell"><Content className="login-content"><Card className="login-card">
        <Space direction="vertical" size="small">
          <Tag color="processing">岗位搜索与变更追踪</Tag><Title level={2}>登录</Title>
          <Paragraph type="secondary">使用预置的求职者或数据维护账号进入应用。</Paragraph>
        </Space>
        {error && <Alert className="login-error" type="error" showIcon message={error} />}
        <Form<LoginValues> layout="vertical" onFinish={login} requiredMark={false}>
          <Form.Item label="用户名" name="username" rules={[{ required: true, message: "请输入用户名" }]}><Input autoComplete="username" /></Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码" }]}><Input.Password autoComplete="current-password" /></Form.Item>
          <Button type="primary" htmlType="submit" loading={submitting} block>登录</Button>
        </Form>
      </Card></Content></Layout>
    );
  }

  return (
    <Layout className="app-shell">
      <Header className="app-header"><Text className="brand">岗位搜索与变更追踪</Text><Space>
        <Tag color={user.role === "maintainer" ? "gold" : "green"}>{user.role === "maintainer" ? "数据维护账号" : "求职者"}</Tag>
        <Text className="header-user">{user.display_name}</Text><Button size="small" onClick={logout}>退出</Button>
      </Space></Header>
      <Content className="app-content"><Card className="hero-card"><Space direction="vertical" size="middle">
        <Tag color="success">登录成功</Tag><Title level={1}>欢迎，{user.display_name}</Title>
        {user.role === "maintainer"
          ? <Alert type="info" showIcon message="数据维护入口已授权" description="真实采集功能将在后续阶段接入。" />
          : <Alert type="info" showIcon message="尚未采集岗位" description="岗位搜索、筛选收藏和关注功能将在后续阶段接入。" />}
      </Space></Card></Content>
    </Layout>
  );
}
