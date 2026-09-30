import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock3,
  FileText,
  FolderLock,
  Hammer,
  LayoutGrid,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Mail,
  Plus,
  Search,
  ShieldCheck,
  Store,
  UploadCloud,
  Waves,
  X,
} from "lucide-react";
import { api } from "./api";

const icons = {
  predial: Building2,
  funcionamiento: Store,
  construccion: Hammer,
};
const date = (value) =>
  new Date(value).toLocaleDateString("es-MX", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
const bytes = (value) =>
  value < 1024 * 1024
    ? `${Math.ceil(value / 1024)} KB`
    : `${(value / 1024 / 1024).toFixed(1)} MB`;

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Waves size={25} />
      </span>
      <span>
        acapulco<span className="brand-sub">PORTAL CIUDADANO</span>
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

function AnalysisResult({ doc, busy, onAnalyze }) {
  const result = doc.analysis || {};
  return <div className="mt-4 text-sm" aria-live="polite">
    <span className={`badge ${doc.analysis_status === 'accepted' ? '' : 'draft'}`}>
      {doc.analysis_status === 'accepted' ? 'Campos mínimos comprobados' : doc.analysis_status === 'not_analyzed' ? 'Pendiente de análisis' : 'Requiere corrección'}
    </span>
    {result.message && <p className="muted mt-3">{result.message}</p>}
    {result.extracted_data && <details className="mt-3">
      <summary className="cursor-pointer text-[#315e4f]">Ver datos extraídos</summary>
      <dl className="mt-2 space-y-2 break-words">{Object.entries(result.extracted_data).filter(([key]) => key !== 'nombre' || !('nombre_completo' in result.extracted_data)).map(([key, value]) => <div key={key}><dt className="text-xs muted">{key.replaceAll('_', ' ')}</dt><dd>{value || 'No identificado'}</dd></div>)}</dl>
    </details>}
    {onAnalyze && <button type="button" className="text-button mt-3" disabled={busy} onClick={() => onAnalyze(doc)}>{busy ? <Spinner/> : <Search size={15}/>} {doc.analysis_status === 'not_analyzed' ? 'Analizar documento' : 'Volver a analizar'}</button>}
  </div>;
}

function DocumentActions({ doc, busy, onUpdate, onDelete, canUpdate }) {
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

function UploadBox({ kind, title, onUpload, busy }) {
  const input = useRef();
  return (
    <div className="upload-box">
      <UploadCloud size={26} />
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

export default function App() {
  const [user, setUser] = useState(null),
    [ready, setReady] = useState(false);
  const [page, setPage] = useState("catalog"),
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
  function navigate(next) {
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
          <span className="status-dot" />
          Acapulco de Juárez<small>Guerrero, México</small>
        </div>
        <span className="nav-label">MI ESPACIO</span>
        <nav>
          {[
            ["catalog", LayoutGrid, "Trámites"],
            ["vault", FolderLock, "Mi Baúl"],
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
          <ShieldCheck size={24} />
          <strong>Tu información, en tu espacio</strong>
          <p>Reutiliza tus documentos sin cargarlos en cada solicitud.</p>
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
                await api("auth/logout/", { method: "POST" });
                setUser(null);
                setDocs([]);
                setApps([]);
                setActive(null);
                setPage("catalog");
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
                  : "Trámites"}
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
          {page === "catalog" && (
            <>
              <section className="hero">
                <div className="hero-content">
                  <span className="eyebrow">
                    MENOS VUELTAS. MÁS TIEMPO PARA TI.
                  </span>
                  <h1>
                    Tu ciudad.
                    <br />
                    <em>Tus trámites, más simples.</em>
                  </h1>
                  <p>
                    Encuentra lo que necesitas, prepara tus documentos
                    <br className="desktop-break" /> y sigue cada paso desde un
                    mismo lugar.
                  </p>
                  <button className="primary" onClick={() => navigate("vault")}>
                    <FolderLock size={17} /> Preparar mi Baúl{" "}
                    <ArrowRight size={17} />
                  </button>
                </div>
                <div className="hero-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="art-card">
                    <div className="art-icon">
                      <FileText size={34} />
                    </div>
                    <span className="art-line" />
                    <span className="art-line short" />
                    <div className="art-check">
                      <Check size={24} />
                    </div>
                  </div>
                  <span className="art-tag">
                    <ShieldCheck size={15} /> Tu espacio digital
                  </span>
                  <Waves className="art-waves" size={140} />
                </div>
              </section>
              <section className="stats-grid">
                <div>
                  <span className="stat-icon">
                    <FolderLock />
                  </span>
                  <p>
                    <strong>{docs.length}</strong>
                    <span>Documentos en tu Baúl</span>
                  </p>
                  <button
                    aria-label="Ver Baúl"
                    onClick={() => navigate("vault")}
                  >
                    <ArrowRight size={19} />
                  </button>
                </div>
                <div>
                  <span className="stat-icon warm">
                    <ClipboardList />
                  </span>
                  <p>
                    <strong>{pending}</strong>
                    <span>Solicitudes enviadas</span>
                  </p>
                  <button
                    aria-label="Ver solicitudes"
                    onClick={() => navigate("applications")}
                  >
                    <ArrowRight size={19} />
                  </button>
                </div>
                <div>
                  <span className="stat-icon blue">
                    <LayoutGrid />
                  </span>
                  <p>
                    <strong>{catalog.length}</strong>
                    <span>Trámites disponibles</span>
                  </p>
                </div>
              </section>
              <section>
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">¿QUÉ NECESITAS HACER HOY?</span>
                    <h2>Catálogo de trámites</h2>
                  </div>
                  <label className="search">
                    <Search size={17} />
                    <input
                      aria-label="Buscar un trámite"
                      placeholder="Buscar un trámite…"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </label>
                </div>
                <div className="procedure-grid">
                  {catalog
                    .filter((p) =>
                      p.name
                        .toLowerCase()
                        .normalize("NFD")
                        .replace(/[\u0300-\u036f]/g, "")
                        .includes(
                          query
                            .toLowerCase()
                            .normalize("NFD")
                            .replace(/[\u0300-\u036f]/g, ""),
                        ),
                    )
                    .map((p, i) => {
                      const Icon = icons[p.id];
                      return (
                        <article className="procedure-card" key={p.id}>
                          <div className="flex justify-between items-center">
                            <span className={`procedure-icon color-${i}`}>
                              <Icon size={26} />
                            </span>
                            <span className="category">{p.category}</span>
                          </div>
                          <h3>{p.name}</h3>
                          <p>{p.description}</p>
                          <div className="requirements">
                            <FileText size={15} />
                            {p.requirements.length} tipos de documento
                          </div>
                          <button
                            disabled={busy || loading}
                            onClick={() => start(p.id)}
                          >
                            Iniciar solicitud <ArrowRight size={18} />
                          </button>
                        </article>
                      );
                    })}
                </div>
                {catalog.length > 0 &&
                  !catalog.some((p) =>
                    p.name.toLowerCase().includes(query.toLowerCase()),
                  ) &&
                  query && (
                    <p className="muted mt-3">
                      Puedes buscar por predial, funcionamiento o construcción.
                    </p>
                  )}
              </section>
              <section className="how-banner">
                <span className="round-icon">
                  <FolderLock />
                </span>
                <div>
                  <h3>Un Baúl. Todos tus documentos.</h3>
                  <p>
                    Cárgalos una vez y reutilízalos cuando inicies una
                    solicitud.
                  </p>
                </div>
                <button
                  className="text-button"
                  onClick={() => navigate("vault")}
                >
                  Conocer mi Baúl <ArrowRight size={17} />
                </button>
              </section>
            </>
          )}
          {page === "vault" && (
            <>
              <div className="section-heading">
                <div>
                  <span className="eyebrow">TU ARCHIVO PERSONAL</span>
                  <h1>Mi Baúl</h1>
                  <p className="muted">
                    Tus documentos disponibles para próximas solicitudes.
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
                    Se analiza localmente el tipo y los campos mínimos antes de guardarlo.
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
            </>
          )}
          {page === "applications" && (
            <>
              <div className="section-heading">
                <div>
                  <span className="eyebrow">CADA PASO, EN UN SOLO LUGAR</span>
                  <h1>Mis solicitudes</h1>
                  <p className="muted">
                    Continúa tus borradores y consulta los folios de recepción.
                  </p>
                </div>
                <button
                  className="secondary"
                  onClick={() => navigate("catalog")}
                >
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
                          {app.folio || "Borrador sin enviar"} ·{" "}
                          {date(app.created_at)}
                        </small>
                      </span>
                      <span
                        className={`badge ${app.status === "draft" ? "draft" : ""}`}
                      >
                        {app.status === "draft" ? "Borrador" : "Recibida"}
                      </span>
                      <ChevronRight size={18} />
                    </button>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <ClipboardList size={42} />
                  <h2>Aquí comienza tu seguimiento</h2>
                  <p>Al iniciar un trámite encontrarás aquí su avance.</p>
                  <button
                    className="primary"
                    onClick={() => navigate("catalog")}
                  >
                    Explorar trámites <ArrowRight size={17} />
                  </button>
                </div>
              )}
            </>
          )}
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
                    ? "Borrador"
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
                      Ir a mi Baúl
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
                          <div className="mt-4">
                            <UploadBox
                              kind={kind}
                              title={
                                doc
                                  ? "Reemplazar con otro archivo"
                                  : `Agregar ${types[kind]}`
                              }
                              onUpload={(k, f) => upload(k, f, active.id)}
                              busy={busy}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </section>
                  <div className="request-actions">
                    <button
                      type="button"
                      className="danger-link"
                      disabled={busy}
                      onClick={() => setCancelDialog(true)}
                    >
                      Cancelar borrador
                    </button>
                    <div className="flex gap-3 flex-wrap">
                      <button
                        type="button"
                        className="secondary"
                        disabled={busy}
                        onClick={() =>
                          action(async () => {
                            setActive(
                              (
                                await api(`applications/${active.id}/`, {
                                  method: "PATCH",
                                  data: { reference },
                                })
                              ).application,
                            );
                            setNotice(
                              "Borrador guardado. Los archivos siguen siendo temporales.",
                            );
                          })
                        }
                      >
                        Guardar borrador
                      </button>
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
          <footer className="footer">
            <span>
              <ShieldCheck size={15} /> Prototipo · Acapulco de Juárez
            </span>
            <p>
              Requisitos demostrativos. Sin conexión municipal, cobros reales ni
              validación oficial de documentos.
            </p>
          </footer>
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
            <h2 id="cancel-title">¿Cancelar este borrador?</h2>
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
                    navigate("applications");
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
