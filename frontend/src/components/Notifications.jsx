import { createPortal } from 'react-dom';
import { CircleAlert, CheckCircle2, X } from 'lucide-react';
import './Notifications.css';

export default function Notifications({ error, notice, onClearError, onClearNotice }) {
  if (!error && !notice) return null;
  return createPortal(<div className="portal-notifications" aria-label="Notificaciones">
    {[{ text: error, type: 'error', title: 'No se pudo completar la operación', close: onClearError },
      { text: notice, type: 'success', title: 'Información del portal', close: onClearNotice }]
      .filter(item => item.text).map(item => <section className={`portal-toast portal-toast-${item.type}`} key={item.type} role={item.type === 'error' ? 'alert' : 'status'} aria-atomic="true">
        <span className="portal-toast-icon" aria-hidden="true">{item.type === 'error' ? <CircleAlert size={22}/> : <CheckCircle2 size={22}/>}</span>
        <div className="portal-toast-content"><strong>{item.title}</strong><p>{item.text}</p></div>
        <button type="button" className="portal-toast-close" onClick={item.close} aria-label={item.type === 'error' ? 'Cerrar notificación de error' : 'Cerrar notificación informativa'}><X size={18}/></button>
      </section>)}
  </div>, document.body);
}
