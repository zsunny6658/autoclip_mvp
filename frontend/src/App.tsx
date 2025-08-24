import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import HomePage from './pages/HomePage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import SettingsPage from './pages/SettingsPage'
import ApiTestPage from './pages/ApiTestPage'
import NetworkTestPage from './pages/NetworkTestPage'
import Header from './components/Header'

const { Content } = Layout

function App() {
  return (
    <Layout>
      <Header />
      <Content>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/project/:id" element={<ProjectDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/api-test" element={<ApiTestPage />} />
          <Route path="/network-test" element={<NetworkTestPage />} />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App