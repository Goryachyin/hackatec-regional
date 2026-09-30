import { useState } from "react";
import { ArrowLeft, ArrowRight, FileText } from "lucide-react";
import { UploadBox } from "../components/Documents";

export default function PagoPredial({ email, navigate }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  return (
    <>
      <button
        type="button"
        className="text-button mb-6"
        onClick={() => navigate("catalog")}
      >
        <ArrowLeft size={16} /> Trámites
      </button>
      <div className="section-heading">
        <div>
          <span className="eyebrow">PATRIMONIO</span>
          <h1>Pago de Predial</h1>
          <p className="muted">
            Prepara un documento que incluya la clave catastral de tu inmueble.
          </p>
        </div>
      </div>
      <section className="panel">
        <h3 className="mb-4">Documento con clave catastral</h3>
        <UploadBox
          kind="clave_catastral"
          title="Carga un documento donde aparezca la clave catastral"
          busy={false}
          onUpload={(_, selected) => {
            setError("");
            if (!/\.(pdf|png|jpe?g)$/i.test(selected.name)) {
              setError("Selecciona un archivo PDF, JPG o PNG.");
              return;
            }
            if (selected.size === 0 || selected.size > 10 * 1024 * 1024) {
              setError("Selecciona un archivo no vacío de hasta 10 MB.");
              return;
            }
            setFile(selected);
          }}
        />
        {error && (
          <p className="error mt-3" role="alert">
            {error}
          </p>
        )}
        {file && (
          <p className="flex gap-2 items-center mt-3 break-all" role="status">
            <FileText size={18} /> Archivo seleccionado: {file.name}
          </p>
        )}
        <p className="muted text-sm mt-3">
          El archivo se mantiene seleccionado en esta pantalla; todavía no se
          envía ni se guarda.
        </p>
        <label className="max-w-lg mt-6">
          Correo electrónico
          <input
            type="email"
            value={email || ""}
            readOnly
            autoComplete="email"
          />
        </label>
        <div className="flex justify-end mt-6">
          <button type="button" className="primary">
            Continuar <ArrowRight size={17} />
          </button>
        </div>
      </section>
    </>
  );
}
