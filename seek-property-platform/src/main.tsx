import { createRoot } from 'react-dom/client';

import App from './App.tsx';
import { initSentry } from './lib/sentry';
import './index.css';

// Initialize Sentry for error tracking
initSentry();

createRoot(document.getElementById("root")!).render(<App />);
