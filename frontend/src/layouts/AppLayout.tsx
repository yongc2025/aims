import { Layout } from 'antd';
import type { ReactNode } from 'react';

const { Header, Sider, Content } = Layout;

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <Layout style={{ minHeight: '100vh', background: '#050816' }}>
      <Sider theme="dark">AIMS</Sider>
      <Layout>
        <Header style={{ background: '#0B1220', color: '#00D4FF' }}>
          AI Market Intelligence System
        </Header>
        <Content>{children}</Content>
      </Layout>
    </Layout>
  );
}
