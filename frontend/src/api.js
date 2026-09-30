let csrf = '';
export async function api(path, { method = 'GET', data } = {}) {
  const form = data instanceof FormData;
  const response = await fetch(`/api/${path}`, {
    method, credentials: 'same-origin',
    headers: { ...(form ? {} : { 'Content-Type': 'application/json' }), ...(method === 'GET' ? {} : { 'X-CSRFToken': csrf }) },
    ...(data ? { body: form ? data : JSON.stringify(data) } : {}),
  });
  const payload = await response.json().catch(() => ({ message: 'No pudimos conectar con el servicio. Inténtalo de nuevo.' }));
  if (!response.ok) throw new Error(payload.message || 'No se pudo completar la operación.');
  if (payload.csrf) csrf = payload.csrf;
  return payload;
}
