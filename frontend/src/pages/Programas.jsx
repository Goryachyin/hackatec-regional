import { useRef, useState } from 'react';
import { ArrowRight, Download, Megaphone, X } from 'lucide-react';

const programs = [
  {
    id: 'guarderia', title: 'Servicio de guardería', category: 'Atención a la niñez',
    image: '/programas/guarderia.png',
    description: 'C.A.D.I. Libertad: atención para hijas e hijos de madres y padres trabajadores, con o sin seguridad social.',
    details: 'Desde los 3 meses hasta los 4 años. Horario de guardería: 7:00 a.m. a 4:00 p.m.',
    contact: 'Informes: 744-220-2773, de 9:00 a.m. a 3:00 p.m. Calle Ignacio Elizondo s/n, esquina Emiliano Zapata, colonia Libertad.',
  },
  {
    id: 'aparatos-funcionales', title: 'Aparatos funcionales', category: 'Apoyos para la movilidad',
    image: '/programas/aparatos-funcionales.png',
    description: 'Información del DIF Acapulco para solicitar sillas de ruedas, muletas, bastones y andaderas.',
    details: 'Consulta en el cartel los requisitos y la documentación necesaria para realizar el trámite.',
    contact: 'Atención en la Coordinación de Trabajo Social, de lunes a viernes de 09:00 a 15:00 horas. Documentos en original y tres copias.',
  },
];

export default function Programas() {
  const dialog = useRef(null);
  const [selected, setSelected] = useState(programs[0]);
  return <>
    <div className="section-heading"><div><span className="eyebrow">DIF ACAPULCO</span><h1>Programas</h1><p className="muted">Conoce los servicios y apoyos para ti y tu familia.</p></div><Megaphone size={30} aria-hidden="true"/></div>
    <div className="program-grid">
      {programs.map(program => <article className="panel program-card" key={program.id}>
        <button type="button" className="program-poster" aria-label={`Ampliar convocatoria: ${program.title}`} onClick={() => { setSelected(program); dialog.current.showModal(); }}>
          <img src={program.image} alt={`Cartel de ${program.title} del DIF Acapulco`} loading="lazy"/>
        </button>
        <div className="program-copy"><span className="eyebrow">{program.category}</span><h2>{program.title}</h2><p>{program.description}</p><p className="muted">{program.details}</p><p className="muted text-sm">{program.contact}</p>
          <button type="button" className="primary" onClick={() => { setSelected(program); dialog.current.showModal(); }}>Ver convocatoria <ArrowRight size={17}/></button>
        </div>
      </article>)}
    </div>
    <p className="muted text-sm mt-6">Información de los carteles publicados. Consulta disponibilidad y vigencia directamente con DIF Acapulco.</p>
    <dialog ref={dialog} className="program-dialog" aria-labelledby="program-title" onClick={event => { if (event.target === dialog.current) dialog.current.close(); }}>
      <header className="program-dialog-header"><h2 id="program-title">{selected.title}</h2><div className="flex gap-4 items-center"><a href={selected.image} download><Download size={19}/><span className="sr-only">Descargar cartel</span></a><button type="button" autoFocus aria-label="Cerrar convocatoria" onClick={() => dialog.current.close()}><X size={24}/></button></div></header>
      <div className="program-dialog-body"><img src={selected.image} alt={`Convocatoria completa: ${selected.title}. ${selected.description} ${selected.details} ${selected.contact}`}/></div>
    </dialog>
  </>;
}
