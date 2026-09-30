import { useState } from "react";

export const dependencyStatus = {
  submitted: "Registrada",
  in_review: "En revisión",
  approved: "Aprobada · simulación",
  rejected: "Rechazada · simulación",
  pending: "Pendiente",
  receiving: "Recibiendo archivos",
};

export default function DependenciesPanel({
  application,
  enabled,
  busy,
  exchange,
}) {
  const [confirmed, setConfirmed] = useState(false);
  if (!application.is_demo || application.procedure !== "funcionamiento")
    return null;
  const delivery = application.delivery || {};
  const received = delivery.status === "received";
  const allSimulated = application.documents.every((d) => d.is_simulated);
  return (
    <section className="panel mt-6" aria-live="polite">
      <span className="badge">Intercambio de demostración</span>
      <h2 className="mt-3">Seguimiento con las dependencias</h2>
      <p className="muted mt-2">
        Envía una copia de los archivos a su respectivo portal.
      </p>
      <p className="mt-3">
        <strong>
          {received
            ? dependencyStatus[delivery.result?.status] ||
              "Recibida por dependencias"
            : `Archivos transferidos: ${delivery.sent_files || 0} de ${application.documents.length}`}
        </strong>
      </p>
      {!delivery.configured && (
        <p className="muted mt-3">
          La conexión con el portal de dependencias todavía no está configurada.
        </p>
      )}
      {!allSimulated && (
        <p className="muted mt-3">
          Esta prueba requiere que todos los documentos del expediente estén
          marcados como simulados.
        </p>
      )}
      {delivery.error && (
        <p role="alert" className="mt-3">
          {delivery.error}
        </p>
      )}
      {!received && (
        <label className="flex gap-3 items-start mt-4">
          <input
            style={{ width: "auto", marginTop: 4 }}
            type="checkbox"
            checked={confirmed}
            disabled={busy}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          <span>
            Confirmar envío de archivos de prueba.
          </span>
        </label>
      )}
      <button
        className="primary mt-4"
        disabled={
          busy ||
          !enabled ||
          !delivery.configured ||
          !allSimulated ||
          (!received && !confirmed)
        }
        onClick={() => exchange(received)}
      >
        {busy
          ? "Comunicando con dependencias…"
          : received
            ? "Actualizar estado"
            : delivery.sent_files
              ? "Continuar envío a dependencias"
              : "Enviar a dependencias"}
      </button>
      {!enabled && (
        <p className="muted mt-2">
          La cuenta necesita tener el modo de demostración habilitado.
        </p>
      )}
      {delivery.result?.areas?.map((area) => (
        <div className="mt-4" key={area.area}>
          <h3>{area.name}</h3>
          <span className="badge">
            {dependencyStatus[area.status] || area.status}
          </span>
          {area.notes && <p className="mt-2">{area.notes}</p>}
        </div>
      ))}
      {delivery.synced_at && (
        <p className="muted text-sm mt-4">
          Última comunicación:{" "}
          {new Date(delivery.synced_at).toLocaleString("es-MX")}. Usa
          “Actualizar estado” para consultar nuevas resoluciones.
        </p>
      )}
    </section>
  );
}
