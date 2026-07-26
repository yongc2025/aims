import { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard';
import Plan2030 from './pages/Plan2030';

type AppPage = 'dashboard' | 'plan2030';

function currentPageFromHash(): AppPage {
  return window.location.hash === '#/plan-2030' ? 'plan2030' : 'dashboard';
}

export default function App() {
  const [page, setPage] = useState<AppPage>(() => currentPageFromHash());

  useEffect(() => {
    const handleHashChange = () => setPage(currentPageFromHash());
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return page === 'plan2030' ? <Plan2030 /> : <Dashboard />;
}
