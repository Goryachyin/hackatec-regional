import { dependencyStatus } from '../components/DependenciesPanel';
import {
  ArrowRight,
  ChevronRight,
  ClipboardList,
  FileText,
  Plus,
} from "lucide-react";
import { date } from "../utils/format";
export default function MisSolicitudes({ apps, busy, navigate, open }) {
  return (
    <>
      <div className="section-heading">
        <div>
          <h1>Mis solicitudes</h1>
          <p className="muted">Consulta tus solicitudes enviadas y sus folios de recepción.</p>
        </div>
        <button className="secondary" onClick={() => navigate("catalog")}>
          <Plus size={17} /> Nueva solicitud
        </button>
      </div>
      {apps.length ? (
        <div className="applications-list">
          {apps.map((app) => (
            <button
              disabled={busy}
              className="application-row"
              key={app.id}
              onClick={() => open(app)}
            >
              <span className="procedure-icon color-0">
                <FileText />
              </span>
              <span className="grow min-w-0">
                <strong>{app.name}</strong>
                <small className="break-all">
                  {app.folio} · {date(app.submitted_at)}
                </small>
              </span>
              <span
                className="badge"
              >
                {dependencyStatus[app.status] || 'Recibida'}{app.is_demo && !['approved', 'rejected'].includes(app.status) ? ' · Demostración' : ''}
              </span>
              <ChevronRight size={18} />
            </button>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <ClipboardList size={42} />
          <h2>Aquí comienza tu seguimiento</h2>
          <p>Aquí aparecerán tus solicitudes cuando las envíes.</p>
          <button className="primary" onClick={() => navigate("catalog")}>
            Explorar trámites <ArrowRight size={17} />
          </button>
        </div>
      )}
    </>
  );
}
