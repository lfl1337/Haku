import { useState, useEffect } from 'react';
import { API_BASE as API } from '../config';

const MAX_RETRIES = 30;
const RETRY_INTERVAL = 1000;

export function useBackendHealth() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let retries = 0;

    async function check() {
      while (retries < MAX_RETRIES && !cancelled) {
        try {
          const res = await fetch(`${API}/health`);
          if (res.ok) {
            if (!cancelled) setReady(true);
            return;
          }
        } catch {
          // Backend not ready yet — keep polling
        }

        retries++;
        if (!cancelled) setAttempt(retries);
        await new Promise(r => setTimeout(r, RETRY_INTERVAL));
      }

      if (!cancelled) {
        setError('Backend konnte nicht gestartet werden.');
      }
    }

    check();
    return () => { cancelled = true; };
  }, []);

  return { ready, error, attempt, maxRetries: MAX_RETRIES };
}
