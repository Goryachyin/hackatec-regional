import Inicio from "./pages/Inicio";
import Tramites from "./pages/Tramites";
import MiBaul from "./pages/MiBaul";
import MisSolicitudes from "./pages/MisSolicitudes";
import { AnalysisResult, UploadBox } from "./components/Documents";
import { useEffect, useState } from "react";
import { Home, ArrowLeft, ArrowRight, Check, CheckCircle2, ChevronRight, ClipboardList, FileText, FolderLock, LayoutGrid, LoaderCircle, LockKeyhole, LogOut, ShieldCheck, Waves, X } from "lucide-react";
import { api } from "./api";

import { date } from "./utils/format";

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Waves size={25} />
      </span>
      <span>
        ACAPULCO<span className="brand-sub">PORTAL CIUDADANO</span>
      </span>
    </div>
  );
}
function Spinner() {
  return <LoaderCircle className="animate-spin" size={18} />;
}

function Auth({ onSuccess }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    curp: "",
    email: "",
    password: "",
    code: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const switchMode = (next) => {
    setMode(next);
    setError("");
    setNotice("");
  };
  async function send(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api(
        `auth/${mode === "register" ? "register" : mode === "verify" ? "verify" : "login"}/`,
        { method: "POST", data: form },
      );
      if (mode === "register") {
        setMode("verify");
        setNotice(result.message);
      } else onSuccess(result.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function resend() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      setNotice(
        (
          await api("auth/resend/", {
            method: "POST",
            data: { email: form.email },
          })
        ).message,
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="auth-shell">
      <section className="auth-intro">
        <Brand />
        <div>
          <span className="eyebrow text-[#c4d9c9]">ACAPULCO DE JUÁREZ</span>
          <h1>
            Tu tiempo importa.
            <br />
            Tus trámites,
            <br />
            <em>más cerca.</em>
          </h1>
          <p>
            Un espacio para organizar tus documentos y dar el siguiente paso,
            sin empezar de nuevo.
          </p>
          <div className="auth-benefits">
            <span>
              <FolderLock /> Documentos en un solo lugar
            </span>
            <span>
              <ClipboardList /> Seguimiento con folio
            </span>
          </div>
        </div>
        <small>Prototipo de desarrollo · HackaTec 2026</small>
      </section>
      <section className="auth-form">
        <div className="auth-card">
          <span className="eyebrow">BIENVENIDO A TU PORTAL</span>
          <h2>
            {mode === "register"
              ? "Crea tu cuenta"
              : mode === "verify"
                ? "Verifica tu correo"
                : "Qué gusto verte aquí"}
          </h2>
          <p className="muted">
            {mode === "verify"
              ? "Introduce el código de 6 dígitos. Tiene una vigencia de 10 minutos."
              : "Accede a tus documentos y solicitudes desde un mismo lugar."}
          </p>
          <form onSubmit={send}>
            {mode === "register" && (
              <label>
                CURP
                <input
                  name="curp"
                  autoComplete="off"
                  maxLength={18}
                  minLength={18}
                  required
                  value={form.curp}
                  onChange={(e) =>
                    setForm({ ...form, curp: e.target.value.toUpperCase() })
                  }
                  placeholder="Tu CURP de 18 caracteres"
                />
                <small>
                  Se revisa el formato; no se consulta RENAPO en esta versión.
                </small>
              </label>
            )}
            <label>
              Correo electrónico
              <input
                name="email"
                type="email"
                autoComplete="email"
                required
                value={form.email}
                onChange={update}
                placeholder="nombre@correo.com"
              />
            </label>
            {mode !== "verify" ? (
              <label>
                Contraseña
                <input
                  name="password"
                  type="password"
                  autoComplete={
                    mode === "register" ? "new-password" : "current-password"
                  }
                  minLength={mode === "register" ? 10 : 1}
                  maxLength={128}
                  required
                  value={form.password}
                  onChange={update}
                  placeholder={
                    mode === "register"
                      ? "Al menos 10 caracteres"
                      : "Tu contraseña"
                  }
                />
              </label>
            ) : (
              <label>
                Código de verificación
                <input
                  name="code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  value={form.code}
                  onChange={update}
                  placeholder="000000"
                  className="tracking-[.5em]"
                />
              </label>
            )}
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            {notice && (
              <p className="success" role="status">
                {notice}
              </p>
            )}
            <button className="primary w-full justify-center" disabled={busy}>
              {busy ? <Spinner /> : <ArrowRight size={18} />}{" "}
              {mode === "register"
                ? "Crear cuenta y enviar código"
                : mode === "verify"
                  ? "Verificar y entrar"
                  : "Iniciar sesión"}
            </button>
          </form>
          <div className="auth-links">
            {mode === "login" ? (
              <>
                <span>
                  ¿Es tu primera vez?{" "}
                  <button onClick={() => switchMode("register")}>
                    Crea una cuenta
                  </button>
                </span>
                <button onClick={() => switchMode("verify")}>
                  Ya tengo un código de verificación
                </button>
              </>
            ) : (
              <>
                <button onClick={() => switchMode("login")}>
                  Volver a iniciar sesión
                </button>
                {mode === "verify" && (
                  <button disabled={busy || !form.email} onClick={resend}>
                    Reenviar código
                  </button>
                )}
              </>
            )}
          </div>
          <div className="disclaimer">
            <LockKeyhole size={16} />
            <span>
              En desarrollo, el código se muestra en la consola del backend. El
              envío a tu bandeja requiere configurar SMTP.
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState(null),
    [ready, setReady] = useState(false);
  const [page, setPage] = useState("home"),
    [catalog, setCatalog] = useState([]),
    [types, setTypes] = useState({});
  const [docs, setDocs] = useState([]),
    [apps, setApps] = useState([]),
    [active, setActive] = useState(null);
  const [query, setQuery] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [uploadKind, setUploadKind] = useState("ine"),
    [showUpload, setShowUpload] = useState(false);
  const [reference, setReference] = useState("");
  const [cancelDialog, setCancelDialog] = useState(false);
  const [cancelDestination, setCancelDestination] = useState("applications");

  useEffect(() => {
    api("auth/session/")
      .then((result) => setUser(result.user))
      .catch((err) => setError(err.message))
      .finally(() => setReady(true));
  }, []);
  async function refresh() {
    const [c, d, a] = await Promise.all([
      api("catalog/"),
      api("documents/"),
      api("applications/"),
    ]);
    setCatalog(c.procedures);
    setTypes(c.document_types);
    setDocs(d.documents);
    setApps(a.applications);
  }
  useEffect(() => {
    if (user) {
      setLoading(true);
      refresh()
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [user]);
  async function action(fn) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  function navigate(next, discarded = false) {
    if (!discarded && active?.status === "draft") {
      setCancelDestination(next);
      setCancelDialog(true);
      return;
    }
    setPage(next);
    setActive(null);
    setError("");
    setNotice("");
    setShowUpload(false);
  }
  async function start(procedure) {
    await action(async () => {
      const result = await api("applications/", {
        method: "POST",
        data: { procedure },
      });
      setActive(result.application);
      setReference("");
      setPage("request");
      await refresh();
    });
  }
  async function open(app) {
    await action(async () => {
      const result = await api(`applications/${app.id}/`);
      setActive(result.application);
      setReference(result.application.reference);
      setPage("request");
    });
  }
  async function upload(kind, file, appId = null) {
    await action(async () => {
      if (file.size > 10 * 1024 * 1024)
        throw new Error("El archivo debe pesar como máximo 10 MB.");
      const form = new FormData();
      form.append("kind", kind);
      form.append("file", file);
      if (appId) form.append("application_id", appId);
      const result = await api("documents/", { method: "POST", data: form });
      if (appId) setActive((await api(`applications/${appId}/`)).application);
      else setShowUpload(false);
      await refresh();
      setNotice(
        appId
          ? `${result.message} Se guardará en tu Baúl al enviar la solicitud.`
          : `${result.message} Documento guardado en tu Baúl.`,
      );
    });
  }
  async function updateDocument(doc, file) {
    await action(async () => {
      if (file.size > 10 * 1024 * 1024) throw new Error('El archivo debe pesar como máximo 10 MB.');
      const form = new FormData();
      form.append('file', file);
      const result = await api(`documents/${doc.id}/`, { method: 'POST', data: form });
      await refresh();
      setNotice(result.message);
    });
  }
  async function deleteDocument(doc) {
    if (!window.confirm(`¿Eliminar "${doc.name}" del Baúl? Si está vinculado a un trámite, se conservará en ese expediente.`)) return;
    await action(async () => {
      const result = await api(`documents/${doc.id}/`, { method: 'DELETE' });
      await refresh();
      setNotice(result.message);
    });
  }
  async function reanalyzeDocument(doc) {
    await action(async () => {
      const result = await api(`documents/${doc.id}/analyze/`, { method: 'POST' });
      await refresh();
      if (active) setActive((await api(`applications/${active.id}/`)).application);
      if (result.document.analysis_status === 'accepted') setNotice(result.message);
      else setError(result.message);
    });
  }
  async function submit(e) {
    e.preventDefault();
    await action(async () => {
      await api(`applications/${active.id}/`, {
        method: "PATCH",
        data: { reference },
      });
      const result = await api(`applications/${active.id}/submit/`, {
        method: "POST",
      });
      setActive(result.application);
      await refresh();
      setNotice("Solicitud registrada. Tus documentos ya están en el Baúl.");
    });
  }
  const pending = apps.filter((a) => a.status === "submitted").length;
  const procedure = active && catalog.find((p) => p.id === active.procedure);
  const complete =
    active &&
    procedure?.requirements.every((kind) =>
      active.documents.some((d) => d.kind === kind && d.analysis_status === 'accepted'),
    );

  if (!ready)
    return (
      <div className="screen-loading">
        <Spinner /> Preparando tu portal…
      </div>
    );
  if (!user)
    return (
      <>
        {error && (
          <div className="error global-error" role="alert">
            {error} Comprueba que Django esté ejecutándose y recarga.
          </div>
        )}
        <Auth
          onSuccess={(value) => {
            setError("");
            setUser(value);
          }}
        />
      </>
    );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="municipality">
        </div>
        <nav>
          {[
            ["home", Home, "Inicio"],
            ["catalog", LayoutGrid, "Trámites"],
            ["vault", FolderLock, "Mis Documentos"],
            ["applications", ClipboardList, "Mis solicitudes"],
          ].map(([id, Icon, label]) => (
            <button
              key={id}
              disabled={busy}
              className={
                page === id || (id === "applications" && page === "request")
                  ? "selected"
                  : ""
              }
              onClick={() => navigate(id)}
            >
              <Icon size={19} />
              {label}
              {id === "vault" && (
                <span className="nav-count">{docs.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
        </div>
        <div className="sidebar-bottom">
          <span className="avatar">{user.email[0].toUpperCase()}</span>
          <div>
            <strong>Mi cuenta ciudadana</strong>
            <small title={user.email}>{user.email}</small>
          </div>
          <button
            disabled={busy}
            aria-label="Cerrar sesión"
            onClick={() =>
              action(async () => {
                if (active?.status === "draft") {
                  if (!window.confirm("La solicitud no se ha enviado y se descartará al cerrar sesión. ¿Continuar?")) return;
                  await api(`applications/${active.id}/`, { method: "DELETE" });
                }
                await api("auth/logout/", { method: "POST" });
                setUser(null);
                setDocs([]);
                setApps([]);
                setActive(null);
                setPage("home");
              })
            }
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            Portal ciudadano <ChevronRight size={14} />{" "}
            <strong>
              {page === "vault"
                ? "Mi Baúl"
                : page === "applications" || page === "request"
                  ? "Mis solicitudes"
                  : page === "home" ? "Inicio" : "Trámites"}
            </strong>
          </span>
          <span className="prototype">ENTORNO DE PRUEBAS</span>
        </header>
        <main className="content">
          {error && (
            <div className="error flex justify-between gap-4" role="alert">
              {error}
              <button aria-label="Cerrar error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div className="success flex gap-2" role="status">
              <CheckCircle2 size={18} />
              {notice}
            </div>
          )}
          {loading && (
            <div className="flex gap-2 muted" role="status">
              <Spinner /> Cargando tu información…
            </div>
          )}
          {page === "home" && <Inicio docs={docs} pending={pending} catalog={catalog} apps={apps} navigate={navigate} open={open} busy={busy} />}
          {page === "catalog" && <Tramites catalog={catalog} query={query} setQuery={setQuery} busy={busy} loading={loading} start={start} navigate={navigate} />}
          {page === "vault" && <MiBaul docs={docs} types={types} showUpload={showUpload} setShowUpload={setShowUpload} uploadKind={uploadKind} setUploadKind={setUploadKind} upload={upload} busy={busy} reanalyzeDocument={reanalyzeDocument} updateDocument={updateDocument} deleteDocument={deleteDocument} />}
          {page === "applications" && <MisSolicitudes apps={apps} busy={busy} navigate={navigate} open={open} />}
          {page === "request" && active && procedure && (
            <>
              <button
                className="text-button mb-6"
                disabled={busy}
                onClick={() => navigate("applications")}
              >
                <ArrowLeft size={16} /> Mis solicitudes
              </button>
              <div className="section-heading">
                <div>
                  <span className="eyebrow">{procedure.category}</span>
                  <h1>{procedure.name}</h1>
                </div>
                <span
                  className={`badge ${active.status === "draft" ? "draft" : ""}`}
                >
                  {active.status === "draft"
                    ? "Sin enviar"
                    : "Solicitud recibida"}
                </span>
              </div>
              {active.status !== "draft" ? (
                <section className="panel confirmation">
                  <span className="confirmation-icon">
                    <CheckCircle2 size={40} />
                  </span>
                  <h2>Tu solicitud quedó registrada</h2>
                  <p>
                    Conserva este folio para consultar tu solicitud o realizar
                    una aclaración.
                  </p>
                  <div className="folio">
                    <small>FOLIO DE SEGUIMIENTO</small>
                    <strong>{active.folio}</strong>
                  </div>
                  <p className="muted">
                    Recibida el {date(active.submitted_at)}. Pendiente de
                    revisión; no representa aprobación ni pago realizado.
                  </p>
                  <div className="flex gap-3 justify-center flex-wrap mt-6">
                    <button
                      className="primary"
                      onClick={() => navigate("applications")}
                    >
                      Ver mis solicitudes
                    </button>
                    <button
                      className="secondary"
                      onClick={() => navigate("vault")}
                    >
                      Ir a mis documentos
                    </button>
                  </div>
                </section>
              ) : (
                <form onSubmit={submit}>
                  <div className="steps">
                    <span className="step active">
                      1 <b>Datos y documentos</b>
                    </span>
                    <span className="step">
                      2 <b>Envío y folio</b>
                    </span>
                  </div>
                  <section className="panel mb-5">
                    <h3 className="mb-4">Datos de la solicitud</h3>
                    <label className="max-w-lg">
                      {procedure.reference_label}
                      {procedure.reference_required ? " *" : " (opcional)"}
                      <input
                        value={reference}
                        onChange={(e) => setReference(e.target.value)}
                        maxLength={100}
                        required={procedure.reference_required}
                        placeholder={procedure.reference_label}
                      />
                    </label>
                  </section>
                  <section className="panel">
                    <h3>Documentos para tu solicitud</h3>
                    <p className="muted text-sm mt-2 mb-5">
                      Los documentos disponibles se toman de tu Baúl. Los nuevos
                      se guardarán allí únicamente al enviar la solicitud.
                    </p>
                    {procedure.requirements.map((kind) => {
                      const doc = active.documents.find((d) => d.kind === kind);
                      const options = docs.filter((d) => d.kind === kind);
                      return (
                        <div className="requirement-row" key={kind}>
                          <div className="flex gap-3 items-start">
                            <span
                              className={`requirement-check ${doc?.analysis_status === 'accepted' ? "done" : ""}`}
                            >
                              {doc ? (
                                <Check size={18} />
                              ) : (
                                <FileText size={18} />
                              )}
                            </span>
                            <div className="grow min-w-0">
                              <h4>{types[kind]}</h4>
                              {doc ? (
                                <>
                                  <p className="truncate">{doc.name}</p>
                                  <small>
                                    {doc.in_vault
                                      ? "Reutilizado de tu Baúl"
                                      : "Temporal · se guardará al enviar"}
                                  </small>
                                  <AnalysisResult doc={doc} busy={busy} onAnalyze={reanalyzeDocument}/>
                                </>
                              ) : (
                                <p className="muted text-sm">
                                  Necesitas agregar este documento.
                                </p>
                              )}
                            </div>
                          </div>
                          {options.length > 0 && (
                            <label className="mt-4 text-sm">
                              Elegir del Baúl
                              <select
                                value={doc?.in_vault ? doc.id : ""}
                                disabled={busy}
                                onChange={(e) =>
                                  e.target.value &&
                                  action(async () => {
                                    const result = await api(
                                      `applications/${active.id}/`,
                                      {
                                        method: "PATCH",
                                        data: {
                                          reference,
                                          document_id: e.target.value,
                                        },
                                      },
                                    );
                                    setActive(result.application);
                                  })
                                }
                              >
                                <option value="">
                                  Selecciona un documento guardado
                                </option>
                                {options.map((d) => (
                                  <option value={d.id} key={d.id}>
                                    {d.name} · {date(d.created_at)}
                                  </option>
                                ))}
                              </select>
                            </label>
                          )}
                          
                        </div>
                      );
                    })}
                  </section>
                  <div className="request-actions">
                    <button
                      type="button"
                      className="danger-link"
                      disabled={busy}
                      onClick={() => { setCancelDestination("applications"); setCancelDialog(true); }}
                    >
                      Cancelar solicitud
                    </button>
                    <div className="flex gap-3 flex-wrap">
                      <button className="primary" disabled={busy || !complete}>
                        {busy ? <Spinner /> : <ArrowRight size={17} />} Enviar
                        solicitud
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </>
          )}
        </main>
      </div>
      {cancelDialog && (
        <div className="modal-backdrop">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-title"
            className="modal"
          >
            <h2 id="cancel-title">¿Descartar esta solicitud sin enviar?</h2>
            <p>
              Se eliminarán sus archivos temporales. Los documentos que ya
              estaban en tu Baúl se conservarán.
            </p>
            <div className="flex gap-3 justify-end mt-6">
              <button
                className="secondary"
                disabled={busy}
                onClick={() => setCancelDialog(false)}
              >
                Continuar solicitud
              </button>
              <button
                className="primary"
                disabled={busy}
                onClick={() =>
                  action(async () => {
                    await api(`applications/${active.id}/`, {
                      method: "DELETE",
                    });
                    setCancelDialog(false);
                    navigate(cancelDestination, true);
                    await refresh();
                  })
                }
              >
                Sí, cancelar
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
