import { ArrowDownToLine, FileText, FolderLock, Plus, X } from "lucide-react";
import { AnalysisResult, DocumentActions, UploadBox } from "../components/Documents";
import { date, bytes } from "../utils/format";
export default function MiBaul({ docs, types, showUpload, setShowUpload, uploadKind, setUploadKind, upload, busy, reanalyzeDocument, updateDocument, deleteDocument }) {
 return (<>
              <div className="section-heading">
                <div>
                  <h1>Mis Documentos</h1>
                  <p className="muted">
                  </p>
                </div>
                <button
                  className="primary"
                  onClick={() => setShowUpload(!showUpload)}
                  disabled={busy}
                >
                  <Plus size={17} /> Agregar documento
                </button>
              </div>
              {showUpload && (
                <section className="panel mb-6">
                  <div className="section-heading">
                    <h3>Guardar un documento</h3>
                    <button
                      aria-label="Cerrar carga"
                      onClick={() => setShowUpload(false)}
                      disabled={busy}
                    >
                      <X />
                    </button>
                  </div>
                  <label className="max-w-md mb-4">
                    Tipo de documento
                    <select
                      value={uploadKind}
                      onChange={(e) => setUploadKind(e.target.value)}
                    >
                      {Object.entries(types).map(([id, name]) => (
                        <option key={id} value={id}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <UploadBox kind={uploadKind} onUpload={upload} busy={busy} />
                  <p className="muted text-sm mt-3">
                    Se analiza el tipo y los campos mínimos antes de guardarlo.
                    Esta revisión no acredita autenticidad oficial.
                  </p>
                </section>
              )}
              {docs.length ? (
                <div className="document-grid">
                  {docs.map((doc) => (
                    <article className="document-card" key={doc.id}>
                      <span className="procedure-icon color-0">
                        <FileText />
                      </span>
                      <span className="badge">En el Baúl</span>
                      <h3>{types[doc.kind] || `Documento anterior (${doc.kind})`}</h3>
                      <p title={doc.name} className="truncate">
                        {doc.name}
                      </p>
                      <small>
                        {bytes(doc.size)} · {date(doc.created_at)}
                      </small>
                      <a href={doc.url}>
                        <ArrowDownToLine size={16} /> Descargar
                      </a>
                      <AnalysisResult doc={doc} busy={busy} onAnalyze={types[doc.kind] ? reanalyzeDocument : null}/>
                      <DocumentActions doc={doc} busy={busy} canUpdate={Boolean(types[doc.kind])} onUpdate={updateDocument} onDelete={deleteDocument}/>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <FolderLock size={42} />
                  <h2>Tu Baúl está listo para empezar</h2>
                  <p>
                    Agrega tu primer documento o guárdalo al completar una
                    solicitud.
                  </p>
                  <button
                    className="primary"
                    onClick={() => setShowUpload(true)}
                  >
                    <Plus size={17} /> Agregar mi primer documento
                  </button>
                </div>
              )}
            </>);
}
