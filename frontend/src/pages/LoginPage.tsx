import { useState } from "react";
import axios from "axios";
import { Alert, Button, Card, Form, Input, Layout, Space, Tag, Typography } from "antd";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

type LoginValues = { username: string; password: string };

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  if (user) return <Navigate to="/jobs" replace />;

  async function submit(values: LoginValues) {
    setSubmitting(true); setError("");
    try { await login(values.username, values.password); navigate("/jobs", { replace: true }); }
    catch (requestError) {
      setError(axios.isAxiosError(requestError) ? requestError.response?.data?.detail ?? "登录服务暂时不可用" : "登录服务暂时不可用");
    } finally { setSubmitting(false); }
  }

  return <Layout className="app-shell"><Layout.Content className="login-content"><Card className="login-card">
    <Space direction="vertical" size="small"><Tag color="processing">岗位搜索与变更追踪</Tag><Typography.Title level={2}>登录</Typography.Title><Typography.Paragraph type="secondary">使用预置的求职者或数据维护账号进入应用。</Typography.Paragraph></Space>
    {error && <Alert className="login-error" type="error" showIcon message={error} />}
    <Form<LoginValues> layout="vertical" onFinish={submit} requiredMark={false}>
      <Form.Item label="用户名" name="username" rules={[{ required: true, message: "请输入用户名" }]}><Input autoComplete="username" /></Form.Item>
      <Form.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码" }]}><Input.Password autoComplete="current-password" /></Form.Item>
      <Button type="primary" htmlType="submit" loading={submitting} block>登录</Button>
    </Form>
  </Card></Layout.Content></Layout>;
}
