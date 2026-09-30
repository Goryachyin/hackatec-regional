import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { ShieldCheck, X } from "lucide-react";
import content from "./privacyContent.json";
import "./PrivacyNotice.css";

export default function PrivacyLink() {
  const dialog = useRef(null);
  const trigger = useRef(null);
  const previousOverflow = useRef(null);
  const titleId = useId();
  function restoreScroll() {
    if (previousOverflow.current !== null) {
      document.body.style.overflow = previousOverflow.current;
      previousOverflow.current = null;
    }
  }
  useEffect(() => () => restoreScroll(), []);
  function show() {
    if (dialog.current.open) return;
    previousOverflow.current = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current.showModal();
    dialog.current.querySelector(".privacy-notice-body").scrollTop = 0;
  }
  function close() {
    dialog.current.close();
  }
  function closed() {
    restoreScroll();
    trigger.current?.focus();
  }
  return (
    <>
      <button
        ref={trigger}
        type="button"
        className="text-button text-sm"
        aria-haspopup="dialog"
        onClick={show}
      >
        Aviso de privacidad
      </button>
      {createPortal(
        <dialog
          ref={dialog}
          className="privacy-notice"
          aria-labelledby={titleId}
          onClose={closed}
          onClick={(e) => {
            if (e.target !== dialog.current) return;
            const bounds = dialog.current.getBoundingClientRect();
            if (
              e.clientX < bounds.left ||
              e.clientX > bounds.right ||
              e.clientY < bounds.top ||
              e.clientY > bounds.bottom
            )
              close();
          }}
        >
          <header className="privacy-notice-header">
            <span className="privacy-notice-icon">
              <ShieldCheck size={24} aria-hidden="true" />
            </span>
            <div>
              <span className="eyebrow">EQUIPO EVA06</span>
              <h2 id={titleId}>Aviso de privacidad</h2>
              <p className="muted">
                Portal ciudadano · Entorno de demostración
              </p>
            </div>
            <button
              type="button"
              className="text-button privacy-notice-close"
              aria-label="Cerrar aviso de privacidad"
              onClick={close}
              autoFocus
            >
              <X size={22} />
            </button>
          </header>
          <div
            className="privacy-notice-body"
            tabIndex={0}
            aria-label="Contenido del aviso de privacidad"
          >
            {content.map((block, index) => {
              if (block.type === "h2") return <h3 key={index}>{block.text}</h3>;
              if (block.type === "notice")
                return (
                  <div key={index} className="privacy-notice-draft">
                    {block.text}
                  </div>
                );
              if (block.type === "li")
                return (
                  <p key={index} className="privacy-notice-item">
                    {block.text}
                  </p>
                );
              return <p key={index}>{block.text}</p>;
            })}
            <a
              href="https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf"
              target="_blank"
              rel="noopener noreferrer"
            >
              Consultar referencia legal (PDF, nueva pestaña)
            </a>
          </div>
          <footer className="privacy-notice-footer">
            <small className="muted">
              Cerrar este aviso no registra consentimiento.
            </small>
            <button type="button" className="primary" onClick={close}>
              Cerrar
            </button>
          </footer>
        </dialog>,
        document.body,
      )}
    </>
  );
}
