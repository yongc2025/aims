import { Layout } from 'antd';

const { Header, Content } = Layout;

export default function App() {
  return (
    <Layout style={{ minHeight: '100vh', background: '#050816' }}>
      <Header style={{ background: '#0B1220', color: '#00D4FF' }}>
        AIMS · AI Market Intelligence System
      </Header>
      <Content style={{ padding: 24, color: '#fff' }}>
        Dashboard loading...
      </Content>
    </Layout>
  );
}
