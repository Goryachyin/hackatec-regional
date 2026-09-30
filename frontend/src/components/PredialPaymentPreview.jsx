import { ArrowLeft, CreditCard, LockKeyhole, ReceiptText } from 'lucide-react';

export default function PredialPaymentPreview({ email, filename, onBack }) {
  return <section className="panel" aria-labelledby="predial-payment-title">
    <button type="button" className="text-button mb-6" onClick={onBack}>
      <ArrowLeft size={16}/> Volver al documento
    </button>
    <div className="section-heading">
      <div>
        <span className="badge">Demostración · Sin cobros</span>
        <h2 id="predial-payment-title" className="mt-3">Pago con tarjeta</h2>
        <p className="muted mt-2">Vista de ejemplo. No ingreses datos bancarios reales.</p>
      </div>
      <CreditCard size={30} aria-hidden="true"/>
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
      <div className="space-y-5">
        <label>Nombre del titular
          <input value="PERSONA DE DEMOSTRACIÓN" readOnly autoComplete="off"/>
        </label>
        <label>Número de tarjeta
          <input value="••••  ••••  ••••  0000" readOnly autoComplete="off"/>
        </label>
        <div className="grid grid-cols-2 gap-4">
          <label>Vencimiento
            <input value="MM / AA" readOnly autoComplete="off"/>
          </label>
          <label>Código de seguridad
            <input value="•••" readOnly autoComplete="off"/>
          </label>
        </div>
        <p className="muted text-sm flex items-start gap-2">
          <LockKeyhole size={18} className="shrink-0" aria-hidden="true"/>
          Los campos son ilustrativos y no admiten captura. No hay conexión con una entidad bancaria.
        </p>
      </div>
      <aside className="rounded-2xl border border-[#dce5d7] bg-[#f5f7f0] p-6">
        <h3 className="flex items-center gap-2"><ReceiptText size={20} aria-hidden="true"/> Resumen de ejemplo</h3>
        <dl className="space-y-4 mt-5">
          <div><dt className="muted text-sm">Concepto</dt><dd>Pago de impuesto predial</dd></div>
          <div><dt className="muted text-sm">Documento seleccionado</dt><dd className="break-all">{filename}</dd></div>
          <div><dt className="muted text-sm">Correo de la cuenta</dt><dd className="break-all">{email || 'No disponible'}</dd></div>
          <div className="border-t border-[#dce5d7] pt-4"><dt className="muted text-sm">Total ficticio para esta demostración</dt><dd className="text-3xl font-semibold mt-1">$1,250.00 <span className="text-sm">MXN</span></dd></div>
        </dl>
        <p className="muted text-sm mt-4">Este importe no corresponde a una consulta de adeudo ni a una tarifa oficial.</p>
        <button type="button" className="primary w-full mt-6" disabled aria-describedby="predial-payment-note">Pagar · No disponible en demostración</button>
        <p id="predial-payment-note" className="muted text-sm mt-3">No se realiza ningún cargo ni se genera un comprobante de pago.</p>
      </aside>
    </div>
  </section>;
}
