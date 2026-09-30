import { ArrowRight, Building2, FileText, FolderLock, Hammer, Search, Store } from "lucide-react";
const icons = {
  predial: Building2,
  funcionamiento: Store,
  construccion: Hammer,
};
export default function Tramites({ catalog, query, setQuery, busy, loading, start, navigate }) {
 return (<>
              <section>
                <div className="section-heading">
                  <div>
                    <h1>Trámites</h1>
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
            </>);
}
