import { Alert, Card, Layout, Space, Tag, Typography } from "antd";

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

export default function App() {
  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <Text className="brand">岗位搜索与变更追踪</Text>
      </Header>
      <Content className="app-content">
        <Card className="hero-card">
          <Space direction="vertical" size="middle">
            <Tag color="processing">基础工程已就绪</Tag>
            <Title level={1}>集中查找岗位，持续看见变化</Title>
            <Paragraph>
              当前完成前端、后端、PostgreSQL 与 Docker 基础结构。真实采集和业务功能将在后续阶段接入。
            </Paragraph>
            <Alert
              type="info"
              showIcon
              message="尚未采集岗位"
              description="后续将由数据维护账号从实习僧和 360 招聘手动发起采集。"
            />
          </Space>
        </Card>
      </Content>
    </Layout>
  );
}

