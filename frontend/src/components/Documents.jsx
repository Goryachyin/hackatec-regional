import PrivacyLink from './PrivacyLink';
import { useRef } from "react";
import { LoaderCircle, Plus, Search, UploadCloud } from "lucide-react";
function Spinner() { return <LoaderCircle className="animate-spin" size={18}/>; }
export function AnalysisResult({ doc, busy, onAnalyze }) {
  const result = doc.analysis || {};
  return <div className="mt-4 text-sm" aria-live="polite">
    <span className={`badge ${doc.analysis_status === 'accepted' ? '' : 'draft'}`}>
      {doc.is_simulated ? 'Revisión simulada' : doc.analysis_status === 'accepted' ? 'Campos mínimos comprobados' : doc.analysis_status === 'received' ? 'Entregado · pendiente de revisión' : doc.analysis_status === 'not_analyzed' ? 'Pendiente de análisis' : 'Requiere corrección'}
    </span>
    {doc.is_simulated && doc.can_use_for_application === false && <p className="muted mt-3">Simulación deshabilitada: vuelve a analizar con el bot o actualiza este documento para utilizarlo.</p>}
    {result.message && <p className="muted mt-3">{result.message}</p>}
    {result.extracted_data && <details className="mt-3">
      <summary className="cursor-pointer text-[#315e4f]">Ver datos extraídos</summary>
      <dl className="mt-2 space-y-2 break-words">{Object.entries(result.extracted_data).filter(([key]) => key !== 'nombre' || !('nombre_completo' in result.extracted_data)).map(([key, value]) => <div key={key}><dt className="text-xs muted">{key.replaceAll('_', ' ')}</dt><dd>{value || 'No identificado'}</dd></div>)}</dl>
    </details>}
    {onAnalyze && <button type="button" className="text-button mt-3" disabled={busy} onClick={() => onAnalyze(doc)}>{busy ? <Spinner/> : <Search size={15}/>} {doc.analysis_status === 'received' ? 'Entregado · pendiente de revisión' : doc.analysis_status === 'not_analyzed' ? 'Analizar documento' : 'Volver a analizar'}</button>}
  </div>;
}

export function DocumentActions({ doc, busy, onUpdate, onDelete, canUpdate }) {
  const input = useRef();
  return <div className="mt-3 flex flex-wrap gap-3">
    {canUpdate && <>
      <input ref={input} type="file" hidden accept=".pdf,.jpg,.jpeg,.png" disabled={busy}
        aria-label={`Actualizar ${doc.name}`} onChange={(e) => {
          const file = e.target.files[0];
          if (file) onUpdate(doc, file);
          e.target.value = '';
        }}/>
      <button type="button" className="text-button" disabled={busy} onClick={() => input.current.click()}>Actualizar documento</button>
    </>}
    <button type="button" className="text-button" disabled={busy} onClick={() => onDelete(doc)}>Eliminar documento</button>
  </div>;
}

export function UploadBox({ kind, title, onUpload, busy }) {
  const input = useRef();
  return (
    <div className="upload-box">
      <UploadCloud size={26} />
      <PrivacyLink/>
      <strong>{title || "Selecciona tu documento"}</strong>
      <span>PDF, JPG o PNG · Máximo 10 MB · PDF hasta 10 páginas</span>
      <input
        ref={input}
        aria-label={`Archivo ${title || kind}`}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        disabled={busy}
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) onUpload(kind, file);
          e.target.value = "";
        }}
      />
      <button
        type="button"
        className="secondary"
        disabled={busy}
        onClick={() => input.current.click()}
      >
        {busy ? <Spinner /> : <Plus size={16} />} {busy ? 'Procesando…' : 'Seleccionar archivo'}
      </button>
    </div>
  );
}

