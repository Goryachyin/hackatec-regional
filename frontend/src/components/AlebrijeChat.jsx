import PrivacyLink from './PrivacyLink';
import { useEffect, useRef, useState } from 'react';
import { Mic, Square, Send, X, Trash2 } from 'lucide-react';
import { api } from '../api';
import './AlebrijeChat.css';

export default function AlebrijeChat({ application, navigate, blocked }) {
  const [opened, setOpened] = useState(false);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState('');
  const recorder = useRef(null), stream = useRef(null), timer = useRef(null), alive = useRef(true);
  const generation = useRef(0), end = useRef(null), input = useRef(null), trigger = useRef(null);
  function stop(discard = false) {
    clearTimeout(timer.current);
    if (discard) generation.current++;
    if (recorder.current?.state === 'recording') recorder.current.stop();
    stream.current?.getTracks().forEach(t => t.stop());
    stream.current = null;
    setRecording(false);
  }
  useEffect(() => { alive.current = true; return () => { alive.current = false; generation.current++; clearTimeout(timer.current); if (recorder.current?.state === 'recording') recorder.current.stop(); stream.current?.getTracks().forEach(t => t.stop()); }; }, []);
  useEffect(() => { if (opened) input.current?.focus(); }, [opened]);
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }); }, [messages, busy]);
  function close() { stop(true); setOpened(false); trigger.current?.focus(); }
  async function send(e) {
    e.preventDefault();
    if (!text.trim() || busy || recording) return;
    const question = text.trim();
    setBusy(true); setError('');
    try {
      const result = await api('chatbot/message/', { method: 'POST', data: {
        message: question, application_id: application?.id || null,
        history: messages.slice(-12).map(m => ({ role: m.role, content: m.content })),
      }});
      if (alive.current) {
        setMessages(previous => [...previous, { role: 'user', content: question }, { role: 'assistant', content: result.answer, actions: result.actions }].slice(-40));
        setText('');
      }
    } catch (err) { if (alive.current) setError(err.message); }
    finally { if (alive.current) setBusy(false); }
  }
  async function record() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { setError('La grabación requiere HTTPS y un navegador compatible. Puedes escribir tu pregunta.'); return; }
    const current = ++generation.current;
    setError(''); setBusy(true);
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!alive.current || current !== generation.current) { audioStream.getTracks().forEach(t => t.stop()); return; }
      stream.current = audioStream;
      const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find(t => MediaRecorder.isTypeSupported(t));
      if (!mime) throw new Error('Este navegador no ofrece un formato de grabación compatible.');
      const r = new MediaRecorder(audioStream, { mimeType: mime, audioBitsPerSecond: 64000 });
      recorder.current = r;
      let chunks = [], size = 0;
      r.ondataavailable = e => { if (e.data.size) { chunks.push(e.data); size += e.data.size; if (size > 2 * 1024 * 1024) stop(); } };
      r.onerror = () => { stop(true); setError('La grabación falló. Intenta de nuevo.'); };
      r.onstop = async () => {
        clearTimeout(timer.current); audioStream.getTracks().forEach(t => t.stop());
        if (!alive.current || current !== generation.current) return;
        setRecording(false);
        if (!size || size > 2 * 1024 * 1024) { setError('Graba una pregunta más breve (hasta 2 MB).'); return; }
        setBusy(true);
        try {
          const form = new FormData(); form.append('audio', new Blob(chunks, { type: mime }), mime.includes('mp4') ? 'voz.mp4' : 'voz.webm');
          chunks = [];
          const result = await api('chatbot/transcribe/', { method: 'POST', data: form });
          if (alive.current && current === generation.current) { setText(old => (old ? old + ' ' : '') + result.text); input.current?.focus(); }
        } catch (err) { if (alive.current && current === generation.current) setError(err.message); }
        finally { if (alive.current) setBusy(false); }
      };
      r.start(1000); setRecording(true);
      timer.current = setTimeout(() => stop(), 60000);
    } catch (err) { stream.current?.getTracks().forEach(t => t.stop()); if (alive.current) setError(err.name === 'NotAllowedError' ? 'No se concedió permiso al micrófono. Puedes escribir tu pregunta.' : err.message); }
    finally { if (alive.current) setBusy(false); }
  }
  return <div className="alebrije-widget">
    {opened && <section className="alebrije-chat" role="dialog" aria-modal="false" aria-labelledby="alebrije-title" onKeyDown={e => { if (e.key === 'Escape') close(); }}>
      <header><div><strong id="alebrije-title">Alebrije Guía</strong><small>Tu acompañante en el portal</small></div><button type="button" aria-label="Cerrar chat" onClick={close}><X size={20}/></button></header>
      <div className="alebrije-context">{application ? `Solicitud: ${application.folio || 'En preparación'}` : 'Orientación del portal y tu cuenta'}</div>
      <div className="alebrije-messages" role="log" aria-live="polite">
        {!messages.length && <><p>¡Hola! Soy Alebrije Guía. Puedo orientarte, consultar tus solicitudes y ayudarte a encontrar una sección.</p><div className="alebrije-suggestions">{['¿Qué necesito para la licencia de funcionamiento?', '¿Cómo van mis solicitudes?', 'Quiero abrir Mis documentos'].map(q => <button key={q} onClick={() => { setText(q); input.current?.focus(); }}>{q}</button>)}</div></>}
        {messages.map((m,i) => <div className={`alebrije-message ${m.role}`} key={i}><small>{m.role === 'user' ? 'Tú' : 'Alebrije Guía'}</small><p>{m.content}</p>{m.actions?.map((a,j) => <button disabled={busy || blocked} key={j} onClick={() => { navigate(a); close(); }}>{a.label}</button>)}</div>)}
        {busy && <p role="status">Procesando…</p>}<div ref={end}/>
      </div>
      <form onSubmit={send} className="alebrije-compose">
        <PrivacyLink/>
        <small>Las consultas, resúmenes necesarios y el audio que grabes se procesan con OpenAI. No envíes contraseñas. El chat no se guarda en tu cuenta.</small>
        {error && <p role="alert" className="alebrije-error">{error}</p>}
        <label htmlFor="alebrije-question">{recording ? 'Grabando · máximo 60 segundos' : 'Escribe o revisa tu transcripción'}</label>
        <textarea ref={input} id="alebrije-question" rows="2" maxLength={2000} value={text} disabled={busy || recording} onChange={e => setText(e.target.value)}/>
        <div className="alebrije-controls"><button type="button" disabled={busy} aria-label={recording ? 'Detener y transcribir' : 'Grabar voz'} onClick={recording ? () => stop() : record}>{recording ? <Square size={18}/> : <Mic size={18}/>}</button><button type="button" aria-label="Limpiar conversación" disabled={busy || recording} onClick={() => { setMessages([]); setError(''); setText(''); }}><Trash2 size={18}/></button><button type="submit" disabled={busy || recording || !text.trim() || text.length > 2000}><Send size={17}/> Enviar</button></div>
      </form>
    </section>}
    <button ref={trigger} className="alebrije-launcher" aria-label={opened ? 'Cerrar Alebrije Guía' : 'Abrir Alebrije Guía'} aria-expanded={opened} onClick={() => opened ? close() : setOpened(true)}><img src="/bot/chatbot-alebrije.png" alt=""/><span>Alebrije Guía</span></button>
  </div>;
}
