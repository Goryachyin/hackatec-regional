import { ArrowRight, Check, ChevronRight, ClipboardList, FileText, FolderLock, LayoutGrid, ShieldCheck, Waves } from "lucide-react";
export default function Inicio({ docs, pending, catalog, apps, navigate, open, busy }) { return <>
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
                  <button className="primary" onClick={() => navigate("catalog")}>
                    <LayoutGrid size={17} /> Explorar trámites{" "}
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

<section className="home-columns">
 <section className="panel">
  <div className="section-heading"><div><span className="eyebrow">TU SIGUIENTE PASO</span><h2>Tus solicitudes recientes</h2></div></div>
  {apps.length ? <div className="applications-list">{apps.slice(0, 3).map(app => <button className="application-row" key={app.id} disabled={busy} onClick={() => open(app)}><FileText size={22}/><span className="grow min-w-0"><strong>{app.name}</strong><small>{app.folio}</small></span><ChevronRight size={18}/></button>)}</div> : <div className="home-empty"><ClipboardList size={30}/><h3>Tu primer trámite comienza aquí</h3><p className="muted">Consulta el catálogo, reúne tus documentos y prepara tu solicitud.</p><button className="text-button" disabled={busy} onClick={() => navigate('catalog')}>Ver trámites disponibles <ArrowRight size={17}/></button></div>}
  {apps.length > 0 && <button className="text-button mt-4" disabled={busy} onClick={() => navigate('applications')}>Ver todas mis solicitudes <ArrowRight size={17}/></button>}
 </section>
 <section className="panel home-guide"><span className="eyebrow">ASÍ DE SENCILLO</span><h2>De tus documentos a tu folio</h2><ol>{[['01', 'Prepara tu Baúl', 'Carga tus documentos para reutilizarlos en próximas solicitudes.'], ['02', 'Elige tu trámite', 'Revisa los requisitos y completa la información solicitada.'], ['03', 'Consulta tu seguimiento', 'Al enviar tu solicitud, conserva el folio para futuras aclaraciones.']].map(([n,title,description]) => <li key={n}><span>{n}</span><div><h3>{title}</h3><p>{description}</p></div></li>)}</ol><button className="text-button" disabled={busy} onClick={() => navigate('vault')}>Ir a mi Baúl <ArrowRight size={17}/></button></section>
</section>
</>; }
