import { Check, FileText } from "lucide-react";
import { UploadBox, AnalysisResult } from "./Documents";

export default function RequirementChecklist({
  procedure,
  application,
  docs,
  types,
  busy,
  upload,
  selectDocument,
  reanalyze,
  readOnly = false,
}) {
  const groups = procedure.requirement_groups || [
    { name: "Documentos requeridos", requirements: procedure.requirements },
  ];
  return (
    <section className="panel">
      <h3>Documentos para tu solicitud</h3>
      <p className="muted text-sm mt-2 mb-5">
        {readOnly
          ? "Documentos incluidos en la solicitud enviada."
          : "Marca tu avance al cargar cada documento. Los archivos nuevos se guardan en tu Baúl al enviar la solicitud."}
      </p>
      {groups.map((group) => {
        const delivered = group.requirements.filter((kind) =>
          application.documents.some((d) => d.kind === kind),
        ).length;
        return (
          <section className="mb-6" key={group.name}>
            <div className="section-heading">
              <h3>{group.name}</h3>
              <span className="badge">
                {delivered} de {group.requirements.length} entregados
              </span>
            </div>
            {group.requirements.map((kind) => {
              const doc = application.documents.find((d) => d.kind === kind);
              const options = docs.filter(
                (d) => d.kind === kind && d.can_use_for_application !== false,
              );
              return (
                <div className="requirement-row" key={kind}>
                  <div className="flex gap-3 items-start">
                    <span className={`requirement-check ${doc ? "done" : ""}`}>
                      {doc ? <Check size={18} /> : <FileText size={18} />}
                    </span>
                    <div className="grow min-w-0">
                      <h4>{types[kind] || kind}</h4>
                      <span className={`badge ${doc ? "" : "draft"}`}>
                        {doc ? "Entregado" : "Pendiente de entregar"}
                      </span>
                      {doc && (
                        <>
                          <p className="break-words mt-2">{doc.name}</p>
                          <a href={doc.url}>Descargar documento</a>
                          <AnalysisResult
                            doc={doc}
                            busy={busy}
                            onAnalyze={!readOnly ? reanalyze : null}
                          />
                        </>
                      )}
                    </div>
                  </div>
                  {!readOnly && (
                    <>
                      {options.length > 0 && (
                        <label className="mt-4 text-sm">
                          Elegir del Baúl
                          <select
                            disabled={busy}
                            value={doc?.in_vault ? doc.id : ""}
                            onChange={(e) =>
                              e.target.value && selectDocument(e.target.value)
                            }
                          >
                            <option value="">
                              Selecciona un documento guardado
                            </option>
                            {options.map((d) => (
                              <option key={d.id} value={d.id}>
                                {d.name}
                              </option>
                            ))}
                          </select>
                        </label>
                      )}
                      {!doc && options.length === 0 && (
                        <div className="mt-4">
                          <UploadBox
                            kind={kind}
                            title={types[kind]}
                            busy={busy}
                            onUpload={(type, file) =>
                              upload(type, file, application.id)
                            }
                          />
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </section>
        );
      })}
    </section>
  );
}
