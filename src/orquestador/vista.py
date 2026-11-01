"""Página local para guardar un mes y consultar el histórico."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import webbrowser

from orquestador.captura import CapturaInvalida, plantilla, recibir_libro
from orquestador.modelos import ETIQUETAS, MODULOS
from orquestador.consulta import DecisionInvalida, decidir, incidentes, resumir
from orquestador.jira import JiraInvalida, enviar
from orquestador.ingesta import EntradaInvalida, leer_libro

_RAIZ = Path(".")


def html_pagina() -> str:
    pagina = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#6750a4">
<title>Consulta mensual de métricas UX</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%236750a4'/%3E%3Crect x='6' y='17' width='5' height='9' rx='1.5' fill='%2334a853'/%3E%3Crect x='13.5' y='11' width='5' height='15' rx='1.5' fill='%23f9ab00'/%3E%3Crect x='21' y='6' width='5' height='20' rx='1.5' fill='%23ea4335'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
<script type="module" src="https://esm.run/@material/web/all.js"></script>
<style>
  :root {
    color-scheme: light;
    --md-ref-typeface-brand: Roboto, sans-serif;
    --md-ref-typeface-plain: Roboto, sans-serif;
    --md-icon-font: "Material Symbols Outlined";
    --md-sys-color-primary: #6750a4;
    --md-sys-color-on-primary: #ffffff;
    --md-sys-color-primary-container: #eaddff;
    --md-sys-color-on-primary-container: #21005d;
    --md-sys-color-secondary: #625b71;
    --md-sys-color-on-secondary: #ffffff;
    --md-sys-color-secondary-container: #e8def8;
    --md-sys-color-on-secondary-container: #1d192b;
    --md-sys-color-tertiary: #7d5260;
    --md-sys-color-on-tertiary: #ffffff;
    --md-sys-color-tertiary-container: #ffd8e4;
    --md-sys-color-on-tertiary-container: #31111d;
    --md-sys-color-error: #b3261e;
    --md-sys-color-on-error: #ffffff;
    --md-sys-color-error-container: #f9dedc;
    --md-sys-color-on-error-container: #410e0b;
    --md-sys-color-background: #fef7ff;
    --md-sys-color-on-background: #1d1b20;
    --md-sys-color-surface: #fef7ff;
    --md-sys-color-on-surface: #1d1b20;
    --md-sys-color-surface-variant: #e7e0ec;
    --md-sys-color-on-surface-variant: #49454f;
    --md-sys-color-outline: #79747e;
    --md-sys-color-outline-variant: #cac4d0;
    --md-sys-color-shadow: #000000;
    --md-sys-color-scrim: #000000;
    --md-sys-color-inverse-surface: #322f35;
    --md-sys-color-inverse-on-surface: #f5eff7;
    --md-sys-color-inverse-primary: #d0bcff;
    --md-sys-color-surface-dim: #ded8e1;
    --md-sys-color-surface-bright: #fef7ff;
    --md-sys-color-surface-container-lowest: #ffffff;
    --md-sys-color-surface-container-low: #f7f2fa;
    --md-sys-color-surface-container: #f3edf7;
    --md-sys-color-surface-container-high: #ece6f0;
    --md-sys-color-surface-container-highest: #e6e0e9;
    --md-sys-color-surface-tint: #6750a4;
    --md-sys-shape-corner-extra-small: 4px;
    --md-sys-shape-corner-small: 8px;
    --md-sys-shape-corner-medium: 12px;
    --md-sys-shape-corner-large: 16px;
    --md-sys-shape-corner-extra-large: 28px;
    --md-sys-shape-corner-full: 999px;
    --md-sys-elevation-1: 0 1px 2px rgb(0 0 0 / .3), 0 1px 3px 1px rgb(0 0 0 / .15);
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: var(--md-ref-typeface-plain); color: var(--md-sys-color-on-surface); background: var(--md-sys-color-surface); }
  .md-typescale-headline-medium { font-size: 1.75rem; line-height: 2.25rem; font-weight: 400; }
  .md-typescale-headline-small { font-size: 1.5rem; line-height: 2rem; font-weight: 400; }
  .md-typescale-title-medium { font-size: 1rem; line-height: 1.5rem; font-weight: 500; letter-spacing: .009rem; }
  .md-typescale-body-large { font-size: 1rem; line-height: 1.5rem; font-weight: 400; letter-spacing: .031rem; }
  .md-typescale-body-medium { font-size: .875rem; line-height: 1.25rem; font-weight: 400; letter-spacing: .016rem; }
  .md-typescale-label-medium { font-size: .75rem; line-height: 1rem; font-weight: 500; letter-spacing: .031rem; }
  header { background: var(--md-sys-color-primary); color: var(--md-sys-color-on-primary); padding: 24px 28px; }
  .marca { max-width: 1100px; margin: 0 auto; }
  header h1 { margin: 0; }
  header p { margin: 8px 0 0; }
  main { display: grid; gap: 16px; max-width: 1100px; margin: 0 auto; padding: 16px 28px 40px; min-width: 0; }
  section { background: var(--md-sys-color-surface-container-lowest); border-radius: var(--md-sys-shape-corner-medium); padding: 16px; box-shadow: var(--md-sys-elevation-1); min-width: 0; }
  h2 { margin: 0 0 16px; }
  h3 { margin: 0 0 8px; }
  .ayuda { margin: 0 0 16px; padding: 16px; background: var(--md-sys-color-primary-container); color: var(--md-sys-color-on-primary-container); border-radius: var(--md-sys-shape-corner-medium); }
  .ayuda p { margin: 0; }
  .ayuda p + p { margin-top: 8px; }
  form, .fila { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; width: 100%; }
  .archivo { display: flex; flex: 1 1 320px; gap: 12px; align-items: center; min-width: 0; }
  .archivo md-outlined-text-field { flex: 1 1 auto; min-width: 0; align-self: center; }
  .fila md-outlined-select { min-width: 12rem; }
  .pestanas { display: flex; gap: 8px; align-items: center; width: 100%; }
  .pestanas md-tabs { flex: 1; min-width: 0; }
  .pestanas #enviar-jira { flex: 0 0 auto; }
  th md-text-button { --md-text-button-container-height: 40px; }
  th.marca, td.marca { width: 48px; text-align: center; white-space: nowrap; }
  td.marca a { color: var(--md-sys-color-primary); font-weight: 500; text-decoration: none; }
  #jira-aviso { margin: 8px 0 0; }
  td.ojo, th.ojo { width: 56px; text-align: right; white-space: nowrap; }
  tr.acordeon td { background: var(--md-sys-color-surface-container-low); }
  tr.acordeon .origen { margin: 0; font-weight: 500; }
  tr.acordeon ul { margin: 8px 0 0; padding-left: 1.1rem; }
  tr.acordeon p { margin: 0; }
  #por-mes, #tipificacion, #historico, #backlog, #excluidos { overflow-x: auto; min-width: 0; max-width: 100%; -webkit-overflow-scrolling: touch; }
  #por-mes table, #historico table, #backlog table, #excluidos table { width: max-content; min-width: 100%; }
  #tipificacion table { width: 100%; min-width: 0; }
  #tipificacion td.sintesis, #tipificacion th:nth-child(2) { white-space: normal; }
  #tipificacion button.hallazgo {
    display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; line-clamp: 3;
    overflow: hidden; width: 100%; margin: 0; padding: 0; border: 0; background: none;
    color: inherit; font: inherit; text-align: left; pointer-events: none;
  }
  #tipificacion td:nth-child(1), #tipificacion th:nth-child(1),
  #tipificacion td:nth-child(5), #tipificacion th:nth-child(5),
  #tipificacion td:nth-child(6), #tipificacion th:nth-child(6),
  #tipificacion td.ojo, #tipificacion th.ojo, #tipificacion td:has(.decision) { white-space: nowrap; }
  #tipificacion td .decision { min-width: 13.5rem; }
  table { border-collapse: collapse; margin-top: 12px; }
  table.listado td, table.listado th { overflow-wrap: anywhere; }
  th, td { text-align: left; padding: 12px 8px; border-bottom: 1px solid var(--md-sys-color-outline-variant); vertical-align: middle; }
  .aviso { min-height: 1.2em; margin: 8px 0 0; color: var(--md-sys-color-error); }
  .vacio { color: var(--md-sys-color-on-surface-variant); }
  .luz { display: inline-flex; align-items: center; justify-content: center; min-width: 5.2rem; min-height: 32px; padding: 0 12px; border-radius: var(--md-sys-shape-corner-small); text-align: center; }
  .verde { background: #ceead6; color: #0d652d; }
  .amarillo { background: #fef7e0; color: #b06000; }
  .rojo { background: var(--md-sys-color-error-container); color: var(--md-sys-color-on-error-container); }
  td .decision { display: flex; flex-flow: row nowrap; gap: 8px; align-items: center; }
  td:has(.decision) { white-space: nowrap; }
  td .decision md-filled-button, td .decision md-outlined-button { flex: 0 0 auto; }
  table.informe th, table.informe td { text-align: center; }
  table.informe td:first-child, table.informe th:first-child { text-align: left; }
  table.informe th.mes { background: var(--md-sys-color-primary); color: var(--md-sys-color-on-primary); font-weight: 500; }
  table.informe th.mes .cubre { display: block; margin-top: 2px; font-weight: 400; }
  tr.total th, tr.total td { background: var(--md-sys-color-secondary-container); color: var(--md-sys-color-on-secondary-container); font-weight: 500; }
  tr.lectura td { color: var(--md-sys-color-on-surface-variant); }
  #decision { width: min(640px, calc(100% - 32px)); }
  #forma-decision { display: grid; gap: 12px; }
  #tipificacion .tarjetas, #historico .tarjetas, #backlog .tarjetas, #excluidos .tarjetas { display: none; }
  .asa { display: none; width: 32px; height: 4px; margin: 0; border-radius: var(--md-sys-shape-corner-full); background: var(--md-sys-color-outline); }
  #hoja[hidden] { display: none; }
  #hoja { position: fixed; inset: 0; z-index: 30; }
  #hoja .velo { position: absolute; inset: 0; border: 0; padding: 0; background: rgb(0 0 0 / .32); animation: aparecer .2s linear; }
  #hoja .panel {
    position: absolute; left: 0; right: 0; bottom: 0; display: grid; gap: 16px; justify-items: center;
    padding: 22px 24px calc(24px + env(safe-area-inset-bottom));
    background: var(--md-sys-color-surface-container-low); color: var(--md-sys-color-on-surface);
    border-radius: var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-large) 0 0;
    animation: subir .3s cubic-bezier(.05, .7, .1, 1);
  }
  #hoja .asa { display: block; }
  #hoja-titulo { margin: 0; width: 100%; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; line-clamp: 3; overflow: hidden; }
  #hoja .acciones { display: flex; gap: 8px; width: 100%; }
  #hoja .acciones md-filled-button, #hoja .acciones md-outlined-button { flex: 1; }
  @keyframes subir { from { transform: translateY(100%); } to { transform: translateY(0); } }
  @keyframes aparecer { from { opacity: 0; } to { opacity: 1; } }
  @media (prefers-reduced-motion: reduce) {
    #hoja .panel, #hoja .velo { animation: none; }
  }
  #forma-decision md-outlined-text-field, #forma-decision md-outlined-select { width: 100%; }
  #decision-caso { margin: 0; color: var(--md-sys-color-on-surface-variant); }
  @media (max-width: 1024px) {
    header, main { padding-left: 20px; padding-right: 20px; }
  }
  @media (max-width: 720px) {
    header, main { padding-left: 16px; padding-right: 16px; }
    form#alta, .fila, .archivo { flex-direction: column; align-items: stretch; }
    .archivo { flex: 0 0 auto; width: 100%; }
    .archivo md-outlined-text-field { flex: 0 0 auto; width: 100%; height: 56px; align-self: stretch; }
    form#alta md-filled-button, form#alta md-text-button, .fila md-outlined-select, .pestanas #enviar-jira { width: 100%; }
    .pestanas { flex-wrap: wrap; }
    section { padding: 16px; }
    th, td { padding: 10px 6px; }
    table.informe { min-width: 40rem; }
    table.informe th, table.informe td { white-space: nowrap; }
    table.informe th:first-child, table.informe td:first-child { white-space: normal; min-width: 7.5rem; max-width: 9rem; }
    table.informe th:not(:first-child), table.informe td:not(:first-child) { min-width: 4.75rem; }
    table.informe tr.lectura td { white-space: normal; max-width: 6.5rem; }
    #por-mes table.informe thead tr:first-child th:first-child,
    #por-mes table.informe tbody th:first-child,
    #por-mes table.informe tbody td:first-child {
      position: sticky; left: 0; z-index: 1; background: var(--md-sys-color-surface-container-lowest);
      box-shadow: 1px 0 0 var(--md-sys-color-outline-variant);
    }
    #por-mes table.informe tr.total th:first-child { background: var(--md-sys-color-secondary-container); }
    #tipificacion, #historico, #backlog, #excluidos { overflow: visible; }
    #tipificacion table, #historico table, #backlog table, #excluidos table { display: none; }
    #tipificacion .tarjetas, #historico .tarjetas, #backlog .tarjetas, #excluidos .tarjetas { display: grid; gap: 12px; }
    .tarjeta { display: grid; gap: 12px; padding: 16px; background: var(--md-sys-color-surface-container-low); color: var(--md-sys-color-on-surface); border-radius: var(--md-sys-shape-corner-medium); }
    #tipificacion .tarjeta { cursor: pointer; }
    #tipificacion .tarjeta .hallazgo { pointer-events: auto; cursor: pointer; color: inherit; font-weight: 500; }
    .tarjeta .cabeza-tarjeta { display: flex; gap: 12px; align-items: flex-start; }
    .tarjeta .texto { margin: 0; font-weight: 500; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; line-clamp: 3; overflow: hidden; }
    .tarjeta .ticket { color: var(--md-sys-color-primary); font-weight: 500; text-decoration: none; }
    .tarjeta .fecha { color: var(--md-sys-color-on-surface-variant); }
    .tarjeta .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; color: var(--md-sys-color-on-surface-variant); }
    .tarjeta .meta .ojo { margin-left: auto; }
    .ordenar-tarjetas, .marcar-todos { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .tarjeta .detalle .origen { margin: 0; font-weight: 500; color: var(--md-sys-color-on-surface); }
    .tarjeta .detalle ul { margin: 8px 0 0; padding-left: 1.1rem; }
    .cabeza-decision { display: grid; justify-items: center; gap: 12px; width: 100%; }
    .cabeza-decision .asa { display: block; }
    #decision-titulo { justify-self: start; width: 100%; }
  }
</style>
</head>
<body>
<header>
  <div class="marca">
    <h1 class="md-typescale-headline-medium">Métricas UX del mes</h1>
    <p class="md-typescale-body-large">Carga las encuestas de CES y CSAT con mayor impacto en B2B. La plataforma te entregará los datos consolidados y agrupará la información recurrente para facilitar su priorización. Los registros de meses anteriores no se verán afectados.</p>
  </div>
</header>
<main>
  <section>
    <form id="alta">
      <div class="archivo">
        <md-outlined-text-field id="archivo-campo" label="Excel del mes" placeholder="Ningún archivo elegido" readonly></md-outlined-text-field>
        <input id="archivo" type="file" accept=".xlsx" hidden>
        <md-filled-tonal-button type="button" id="elegir-archivo">Elegir archivo</md-filled-tonal-button>
      </div>
      <md-filled-button type="submit">Subir Excel</md-filled-button>
      <md-text-button href="/plantilla/feedback_response_2026-01.xlsx">Descargar plantilla</md-text-button>
    </form>
    <p class="aviso md-typescale-body-medium" id="aviso"></p>
  </section>
  <section>
    <h2 class="md-typescale-headline-small">Total e histórico</h2>
    <div class="fila">
      <md-outlined-select id="corte" label="Ver">
        <md-select-option value="mes" selected><div slot="headline">Por mes</div></md-select-option>
        <md-select-option value="trimestre"><div slot="headline">Trimestre</div></md-select-option>
        <md-select-option value="semestre"><div slot="headline">Semestre</div></md-select-option>
      </md-outlined-select>
      <md-outlined-select id="periodo" label="Periodo">
        <md-select-option value="todos" selected><div slot="headline">Todos</div></md-select-option>
      </md-outlined-select>
      <input id="mes" type="month" value="2026-07" hidden>
    </div>
    <div id="por-mes"></div>
  </section>
  <section id="listados">
    <div class="pestanas">
      <md-tabs id="vistas">
        <md-primary-tab data-panel="guardar">Guardar el mes</md-primary-tab>
        <md-primary-tab data-panel="historico">Tipificados</md-primary-tab>
        <md-primary-tab data-panel="backlog">Backlog</md-primary-tab>
        <md-primary-tab data-panel="excluidos">Excluidos</md-primary-tab>
      </md-tabs>
      <md-filled-button type="button" id="enviar-jira" hidden disabled>Enviar a Jira</md-filled-button>
    </div>
    <p class="aviso md-typescale-body-medium" id="jira-aviso"></p>
    <div id="guardar">
      <h3 class="md-typescale-title-medium">Hallazgos del mes</h3>
      <div class="ayuda md-typescale-body-medium">
        <p>En esta tabla encontrarás los hallazgos de mayor impacto en la plataforma. La información está sintetizada y te permite visualizar el nivel de criticidad junto con las frases originales para facilitar su auditoría.</p>
        <p>Desde aquí puedes decidir si un hallazgo se tipifica o se excluye. Si la información excluida se repite por más de dos meses, volverá a priorizarse. Una vez tipificados, podrás enviarlos a Jira para gestionar su desarrollo y hacer seguimiento a los tickets desde esta misma vista.</p>
      </div>
      <div id="tipificacion"></div>
    </div>
    <div id="historico" hidden></div>
    <div id="backlog" hidden></div>
    <div id="excluidos" hidden></div>
  </section>
</main>
<md-dialog id="decision" type="alert">
  <div slot="headline" class="cabeza-decision">
    <span class="asa"></span>
    <span id="decision-titulo"></span>
  </div>
  <form id="forma-decision" slot="content">
    <md-outlined-text-field id="decision-sintesis" label="Síntesis" type="textarea" rows="2"></md-outlined-text-field>
    <md-outlined-select id="decision-modulo" label="Módulo"></md-outlined-select>
    <md-outlined-select id="decision-etiqueta" label="Etiqueta"></md-outlined-select>
    <md-outlined-text-field id="decision-motivo" label="Por qué" type="textarea" rows="3"></md-outlined-text-field>
    <p class="aviso md-typescale-body-medium" id="decision-aviso"></p>
  </form>
  <div slot="actions">
    <md-text-button type="button" id="decision-cancelar">Cancelar</md-text-button>
    <md-filled-button type="button" id="decision-confirmar">Confirmar</md-filled-button>
  </div>
</md-dialog>
<div id="hoja" hidden>
  <button type="button" class="velo" data-cerrar-hoja aria-label="Cerrar"></button>
  <div class="panel" role="dialog" aria-modal="true" aria-labelledby="hoja-titulo">
    <span class="asa"></span>
    <p id="hoja-titulo" class="md-typescale-body-large"></p>
    <div class="acciones">
      <md-filled-button type="button" data-resultado="aceptado">Se queda</md-filled-button>
      <md-outlined-button type="button" data-resultado="rechazado">Se va</md-outlined-button>
    </div>
  </div>
</div>
<script>
const nombres = {creacion: "Creación de Vacantes", catalogo: "Catálogo", gestion: "Gestión de Vacantes"};
const modulosOficiales = /*MODULOS*/[];
const etiquetasOficiales = /*ETIQUETAS*/[];
const aviso = document.querySelector("#aviso");
const dialogo = document.querySelector("#decision");
let pendiente = null;
const listo = Promise.all([
  customElements.whenDefined("md-outlined-select"),
  customElements.whenDefined("md-outlined-text-field"),
  customElements.whenDefined("md-filled-button"),
  customElements.whenDefined("md-tabs"),
  customElements.whenDefined("md-dialog"),
  customElements.whenDefined("md-checkbox"),
]);
document.querySelector("#corte").addEventListener("change", cambiarCorte);
document.querySelector("#periodo").addEventListener("change", cambiarPeriodo);
document.querySelector("#alta").addEventListener("submit", subir);
document.querySelector("#archivo").addEventListener("change", mostrarArchivo);
document.querySelector("#elegir-archivo").addEventListener("click", () => document.querySelector("#archivo").click());
document.querySelector("#tipificacion").addEventListener("click", abrirDecision);
document.querySelector("#hoja").addEventListener("click", elegirDesdeHoja);
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && !document.querySelector("#hoja").hidden) cerrarHoja();
});
document.querySelector("#listados").addEventListener("click", verDecision);
customElements.whenDefined("md-dialog").then(estiloHojaDialogo);
document.querySelector("#listados").addEventListener("change", marcarJira);
document.querySelector("#vistas").addEventListener("change", cambiarVista);
document.querySelector("#decision-confirmar").addEventListener("click", confirmarDecision);
document.querySelector("#decision-cancelar").addEventListener("click", () => dialogo.close());
cargar();

const consultaPublica = /*CONSULTA_PUBLICA*/null;
let consulta = null;
let orden = {clave: "criticidad", sentido: 1};
const pesoColor = {rojo: 0, amarillo: 1, verde: 2};
async function cargar() {
  await listo;
  aviso.textContent = "";
  const mes = document.querySelector("#mes").value;
  try {
    const respuesta = await fetch("/api/consulta?mes=" + encodeURIComponent(mes));
    if (!respuesta.ok) throw new Error();
    consulta = await respuesta.json();
  } catch (error) {
    consulta = consultaPublica;
  }
  if (!consulta) {
    aviso.textContent = "No se pudo cargar la consulta.";
    return;
  }
  await llenarPeriodos();
  pintarHistorico();
  document.querySelector("#tipificacion").innerHTML = tablaTipificacion(consulta.tipificacion);
  pintarListados();
}
function pintarListados() {
  if (!consulta) return;
  document.querySelector("#historico").innerHTML = tablaHistorico(consulta.historico);
  document.querySelector("#backlog").innerHTML = tablaBacklog(consulta.backlog);
  document.querySelector("#excluidos").innerHTML = tablaExcluidos(consulta.excluidos);
  actualizarEnvioJira();
}
function ordenarHallazgos(items) {
  const fecha = (item) => String(item.mes || "");
  const color = (item) => pesoColor[item.criticidad] ?? 3;
  return [...items].sort((a, b) => {
    const porFecha = fecha(a).localeCompare(fecha(b));
    const porColor = color(a) - color(b);
    if (orden.clave === "fecha") return porFecha * orden.sentido || porColor;
    return porColor * orden.sentido || -porFecha;
  });
}
function marcaOrden(clave) {
  if (orden.clave !== clave) return "";
  return orden.sentido > 0 ? " ▲" : " ▼";
}
function cabezaOrden(clave, titulo) {
  return `<th><md-text-button type="button" class="orden" data-orden="${clave}">${titulo}${marcaOrden(clave)}</md-text-button></th>`;
}
function verDecision(evento) {
  const ordenar = evento.target.closest("[data-orden]");
  if (ordenar) {
    const clave = ordenar.dataset.orden;
    orden.sentido = orden.clave === clave ? orden.sentido * -1 : 1;
    orden.clave = clave;
    pintarListados();
    return;
  }
  if (evento.target.closest("#enviar-jira")) {
    enviarJira();
    return;
  }
  const boton = evento.target.closest("[data-ojo]");
  if (!boton) return;
  const fila = boton.closest("tr");
  const panel = (fila && fila.nextElementSibling) || (boton.closest(".tarjeta") && boton.closest(".tarjeta").querySelector(".detalle"));
  if (!panel || !(panel.classList.contains("acordeon") || panel.classList.contains("detalle"))) return;
  panel.hidden = !panel.hidden;
  boton.setAttribute("aria-pressed", panel.hidden ? "false" : "true");
}
function textoDecision(item) {
  if (item.resultado === "aceptado") return item.motivo ? "Se queda. " + item.motivo : "Se queda";
  if (item.resultado === "rechazado") return item.motivo ? "Se va. " + item.motivo : "Se va";
  return "Sin decidir";
}
function comentariosDe(item) {
  if (Array.isArray(item.comentarios) && item.comentarios.length) return item.comentarios.filter((texto) => String(texto).trim());
  const uno = item.comentario || item.sintesis || "";
  return uno ? [uno] : [];
}
function lineasHallazgo(item) {
  const textos = comentariosDe(item);
  const veces = Number(item.conteo) || textos.length;
  if (!textos.length) return [];
  if (textos.length >= veces) return textos;
  if (textos.length === 1) return Array.from({length: veces}, () => textos[0]);
  return textos;
}
function botonHallazgos() {
  return `<md-icon-button type="button" data-ojo aria-label="Ver hallazgos" aria-pressed="false"><md-icon>visibility</md-icon></md-icon-button>`;
}
function filaHallazgos(item) {
  const lista = lineasHallazgo(item).map((texto) => `<li>${esc(texto)}</li>`).join("");
  return `<tr class="acordeon" hidden><td colspan="8"><p class="origen">Hallazgos</p><ul>${lista}</ul></td></tr>`;
}
function botonOjo() {
  return `<md-icon-button type="button" data-ojo aria-label="Ver comentarios" aria-pressed="false"><md-icon>visibility</md-icon></md-icon-button>`;
}
function filaAcordeon(item, columnas, conDecision = true) {
  const lista = lineasHallazgo(item).map((texto) => `<li>${esc(texto)}</li>`).join("");
  const nota = conDecision ? esc(textoDecision(item)) : (item.motivo ? esc(item.motivo) : "");
  const decision = nota ? `<p>${nota}</p>` : "";
  return `<tr class="acordeon" hidden><td colspan="${columnas}">${decision}<p class="origen">Hallazgos</p><ul>${lista}</ul></td></tr>`;
}
function cajasJira() {
  return [...document.querySelectorAll("#historico [data-jira]")].filter((caja) => {
    const bloque = caja.closest("table, .tarjetas");
    return bloque && getComputedStyle(bloque).display !== "none";
  });
}
function marcarJira(evento) {
  if (evento.target.id === "jira-todos" || evento.target.id === "jira-todos-tarjetas") {
    const activo = evento.target.checked;
    document.querySelectorAll("#historico [data-jira]").forEach((caja) => { caja.checked = activo; });
  } else if (evento.target.dataset && evento.target.dataset.jira !== undefined) {
    const caja = evento.target;
    document.querySelectorAll("#historico [data-jira]").forEach((otra) => {
      if (otra.dataset.id === caja.dataset.id && otra.dataset.mes === caja.dataset.mes) otra.checked = caja.checked;
    });
  }
  actualizarEnvioJira();
}
function actualizarEnvioJira() {
  const boton = document.querySelector("#enviar-jira");
  const cajas = cajasJira();
  const marcadas = cajas.filter((caja) => caja.checked).length;
  if (boton) boton.disabled = marcadas === 0;
  const todosMarcados = cajas.length > 0 && marcadas === cajas.length;
  document.querySelectorAll("#jira-todos, #jira-todos-tarjetas").forEach((todos) => { todos.checked = todosMarcados; });
}
function mostrarPanel(panel) {
  const tabs = document.querySelector("#vistas");
  const lista = [...tabs.querySelectorAll("md-primary-tab")];
  const indice = lista.findIndex((item) => item.dataset.panel === panel);
  if (indice >= 0 && tabs.activeTabIndex !== indice) tabs.activeTabIndex = indice;
  document.querySelector("#historico").hidden = panel !== "historico";
  document.querySelector("#backlog").hidden = panel !== "backlog";
  document.querySelector("#excluidos").hidden = panel !== "excluidos";
  document.querySelector("#guardar").hidden = panel !== "guardar";
  document.querySelector("#enviar-jira").hidden = panel !== "historico";
}
function cambiarVista() {
  const tabs = document.querySelector("#vistas");
  const tab = tabs.querySelectorAll("md-primary-tab")[tabs.activeTabIndex];
  if (tab) mostrarPanel(tab.dataset.panel);
}
async function enviarJira() {
  const avisoJira = document.querySelector("#jira-aviso");
  const marcas = cajasJira().filter((caja) => caja.checked);
  if (!marcas.length) {
    avisoJira.textContent = "Selecciona al menos un caso.";
    return;
  }
  const boton = document.querySelector("#enviar-jira");
  boton.disabled = true;
  avisoJira.textContent = "Enviando a Jira…";
  try {
    const respuesta = await fetch("/api/jira", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({items: marcas.map((caja) => ({mes: caja.dataset.mes, id: caja.dataset.id}))})
    });
    const datos = await respuesta.json();
    if (!respuesta.ok) {
      avisoJira.textContent = datos.error || "No se pudo crear el ticket.";
      return;
    }
    const claves = (datos.creados || []).map((item) => item.clave).filter(Boolean).join(", ");
    const fallos = (datos.errores || []).map((item) => item.error).filter(Boolean).join(" ");
    await cargar();
    if ((datos.creados || []).length && !(datos.errores || []).length) {
      mostrarPanel("backlog");
    }
    document.querySelector("#jira-aviso").textContent = [claves ? claves + " en Jira." : "", fallos].filter(Boolean).join(" ");
  } catch (error) {
    avisoJira.textContent = "No se pudo crear el ticket.";
  } finally {
    actualizarEnvioJira();
  }
}
async function cambiarCorte() {
  document.querySelector("#periodo").value = "todos";
  await llenarPeriodos();
  pintarHistorico();
}
function cambiarPeriodo() {
  const periodo = document.querySelector("#periodo").value;
  if (/^\\d{4}-\\d{2}$/.test(periodo) && periodo !== document.querySelector("#mes").value) {
    document.querySelector("#mes").value = periodo;
    cargar();
    return;
  }
  pintarHistorico();
}
async function llenarPeriodos() {
  const meses = consulta && consulta.meses ? consulta.meses : [];
  const corte = document.querySelector("#corte").value;
  const actual = document.querySelector("#periodo").value;
  const opciones = [{id: "todos", titulo: "Todos"}].concat(columnas(meses, corte, "todos").map((columna) => ({id: columna.id, titulo: columna.titulo})));
  const periodo = document.querySelector("#periodo");
  const elegido = opciones.some((opcion) => opcion.id === actual) ? actual : "todos";
  periodo.innerHTML = opciones.map((opcion) => `<md-select-option value="${esc(opcion.id)}"><div slot="headline">${esc(opcion.titulo)}</div></md-select-option>`).join("");
  await periodo.updateComplete;
  periodo.value = "";
  periodo.value = elegido;
}
function pintarHistorico() {
  if (!consulta) return;
  document.querySelector("#por-mes").innerHTML = tablaPorMes(consulta.por_mes, document.querySelector("#corte").value, document.querySelector("#periodo").value);
}
function mostrarArchivo() {
  const archivo = document.querySelector("#archivo").files[0];
  document.querySelector("#archivo-campo").value = archivo ? archivo.name : "";
}
async function subir(evento) {
  evento.preventDefault();
  aviso.textContent = "";
  const archivo = document.querySelector("#archivo").files[0];
  if (!archivo) { aviso.textContent = "Elige el Excel del mes."; return; }
  const respuesta = await fetch("/api/guardar", {
    method: "POST",
    headers: {"X-Nombre": archivo.name},
    body: await archivo.arrayBuffer()
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) { aviso.textContent = datos.error || "No se pudo guardar."; return; }
  document.querySelector("#mes").value = datos.mes;
  aviso.textContent = "Excel guardado. Corre el ciclo para que entre al total y al histórico.";
  cargar();
}
const ordenP = ["creacion", "catalogo", "gestion"];
const nombresMes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
function nombreMes(iso) {
  const partes = iso.split("-");
  const nombre = nombresMes[Number(partes[1]) - 1] || iso;
  return nombre.charAt(0).toUpperCase() + nombre.slice(1) + " " + partes[0];
}
function coma(numero, decimales) {
  return numero.toFixed(decimales).replace(".", ",");
}
function valorCelda(item, metrica) {
  if (!item || item.valor == null || item.n <= 0) return "";
  if (metrica === "CES") return coma(item.valor, 2);
  return coma(item.valor / 5 * 100, 2) + "%";
}
function lectura(item, metrica) {
  if (!item) return "";
  if (metrica === "CES") return coma(item.valor, 1) + " de 5 en facilidad de uso";
  return coma(item.valor * 2, 1) + " de cada 10 usuarios";
}
function ponderar(partes) {
  const utiles = partes.filter((item) => item && item.valor != null && item.n > 0);
  if (!utiles.length) return null;
  const n = utiles.reduce((suma, item) => suma + item.n, 0);
  const valor = Math.round(utiles.reduce((suma, item) => suma + item.valor * item.n, 0) / n * 100) / 100;
  return {valor, n};
}
function tituloTrimestre(numero, anio) {
  const ordinal = {1: "1.er", 2: "2.º", 3: "3.er", 4: "4.º"}[numero];
  return ordinal + " trimestre " + anio;
}
function tituloSemestre(numero, anio) {
  return (numero === 1 ? "1.er" : "2.º") + " semestre " + anio;
}
function mesesQueCubre(meses) {
  const anios = new Set(meses.map((mes) => mes.slice(0, 4)));
  const etiquetas = meses.map((mes) => anios.size === 1 ? nombreMes(mes).replace(/ \\d{4}$/, "") : nombreMes(mes));
  if (etiquetas.length <= 1) return etiquetas[0] || "";
  return etiquetas.slice(0, -1).join(", ") + " y " + etiquetas[etiquetas.length - 1];
}
function columnas(meses, corte, periodo) {
  if (corte === "mes") {
    const lista = periodo === "todos" ? meses : meses.filter((mes) => mes === periodo);
    return lista.map((mes) => ({id: mes, titulo: nombreMes(mes), meses: [mes]}));
  }
  const grupos = [];
  const mapa = {};
  meses.forEach((mes) => {
    const anio = mes.slice(0, 4);
    const numeroMes = Number(mes.slice(5));
    const grupo = corte === "trimestre"
      ? {id: anio + "-T" + Math.ceil(numeroMes / 3), titulo: tituloTrimestre(Math.ceil(numeroMes / 3), anio)}
      : {id: anio + "-S" + (numeroMes <= 6 ? 1 : 2), titulo: tituloSemestre(numeroMes <= 6 ? 1 : 2, anio)};
    if (periodo !== "todos" && grupo.id !== periodo) return;
    if (!mapa[grupo.id]) {
      mapa[grupo.id] = {id: grupo.id, titulo: grupo.titulo, meses: []};
      grupos.push(mapa[grupo.id]);
    }
    mapa[grupo.id].meses.push(mes);
  });
  return grupos;
}
function tablaPorMes(items, corte, periodo) {
  if (!items || !items.length) return "<p class=\\"vacio\\">Sin meses corridos.</p>";
  const meses = [...new Set(items.map((item) => item.mes))].sort();
  const visibles = columnas(meses, corte || "mes", periodo || "todos");
  if (!visibles.length) return "<p class=\\"vacio\\">No hay datos en ese periodo.</p>";
  const metricas = ["CSAT", "CES"];
  const indice = {};
  items.forEach((item) => { indice[item.mes + "|" + item.pestana + "|" + item.nombre] = item; });
  const leer = (columna, pestana, metrica) => ponderar(columna.meses.map((mes) => indice[mes + "|" + pestana + "|" + metrica]));
  const totalDe = (columna, metrica) => ponderar(ordenP.map((pestana) => leer(columna, pestana, metrica)));
  const mesesCabeza = visibles.map((columna) => {
    const cubre = corte !== "mes" ? `<span class="cubre">${esc(mesesQueCubre(columna.meses))}</span>` : "";
    return `<th class="mes" colspan="${metricas.length}">${esc(columna.titulo)}${cubre}</th>`;
  }).join("");
  const metricasCabeza = visibles.map(() => metricas.map((metrica) => `<th>${esc(metrica)}</th>`).join("")).join("");
  const filaArea = (pestana) => `<tr><th>${esc(nombres[pestana])}</th>${visibles.map((columna) => metricas.map((metrica) => `<td>${valorCelda(leer(columna, pestana, metrica), metrica)}</td>`).join("")).join("")}</tr>`;
  const filaTotal = `<tr class="total"><th>Total</th>${visibles.map((columna) => metricas.map((metrica) => `<td>${valorCelda(totalDe(columna, metrica), metrica)}</td>`).join("")).join("")}</tr>`;
  const filaLectura = `<tr class="lectura"><th></th>${visibles.map((columna) => metricas.map((metrica) => `<td>${esc(lectura(totalDe(columna, metrica), metrica))}</td>`).join("")).join("")}</tr>`;
  const filaMuestra = `<tr><th>Cuántas personas evaluaron</th>${visibles.map((columna) => metricas.map((metrica) => { const total = totalDe(columna, metrica); return `<td>${total ? total.n : ""}</td>`; }).join("")).join("")}</tr>`;
  return `<table class="informe"><thead><tr><th rowspan="2"></th>${mesesCabeza}</tr><tr>${metricasCabeza}</tr></thead><tbody>${ordenP.map(filaArea).join("")}${filaTotal}${filaLectura}${filaMuestra}</tbody></table>`;
}
function tablaTipificacion(items) {
  if (!items || !items.length) return "<p class=\\"vacio\\">Este mes todavía no tiene incidentes. Corre el ciclo después de guardar.</p>";
  const pendientes = items.filter((item) => item.resultado !== "aceptado" && item.resultado !== "rechazado");
  if (!pendientes.length) return "<p class=\\"vacio\\">Los que se quedan están en Tipificados y los que se van, en Excluidos.</p>";
  const cuerpo = pendientes.map((item) => {
    const titulo = item.sintesis || item.comentario;
    return `<tr><td>${esc(textoFecha(item))}</td><td class="sintesis"><button type="button" class="hallazgo" data-id="${esc(item.id)}" data-abrir="1">${esc(titulo)}</button></td><td>${esc(item.modulo || "")}</td><td>${esc(item.etiqueta || "")}</td><td><span class="luz md-typescale-label-medium ${esc(item.criticidad)}">${esc(item.criticidad || "sin dato")}</span></td><td>${item.conteo ?? 0}</td><td class="ojo">${botonHallazgos()}</td><td><div class="decision"><md-filled-button type="button" data-id="${esc(item.id)}" data-resultado="aceptado" data-motivo="${esc(item.motivo || "")}">Se queda</md-filled-button><md-outlined-button type="button" data-id="${esc(item.id)}" data-resultado="rechazado" data-motivo="${esc(item.motivo || "")}">Se va</md-outlined-button></div></td></tr>${filaHallazgos(item)}`;
  }).join("");
  const tarjetas = pendientes.map(tarjetaTipificacion).join("");
  return `<table><thead><tr><th>Fecha</th><th>Síntesis</th><th>Módulo</th><th>Etiqueta</th><th>Criticidad</th><th>Veces</th><th class="ojo"></th><th></th></tr></thead><tbody>${cuerpo}</tbody></table><div class="tarjetas">${tarjetas}</div>`;
}
function textoFecha(item) {
  return item.mes ? nombreMes(item.mes) : "";
}
function tarjetaTipificacion(item) {
  const titulo = item.sintesis || item.comentario || "";
  const lista = lineasHallazgo(item).map((texto) => `<li>${esc(texto)}</li>`).join("");
  return `<article class="tarjeta"><span class="fecha md-typescale-label-medium">${esc(textoFecha(item))}</span><button type="button" class="hallazgo" data-id="${esc(item.id)}" data-abrir="1">${esc(titulo)}</button><div class="meta md-typescale-label-medium"><span class="luz ${esc(item.criticidad)}">${esc(item.criticidad || "sin dato")}</span><span>${item.conteo ?? 0}</span><span>${esc(item.modulo || "Sin definir")}</span><span>${esc(item.etiqueta || "Sin definir")}</span><span class="ojo">${botonHallazgos()}</span></div><div class="detalle" hidden><p class="origen">Hallazgos</p><ul>${lista}</ul></div></article>`;
}
async function ponerOpciones(select, valores, actual) {
  const elegido = actual || "";
  const extras = elegido && !valores.includes(elegido) ? [elegido] : [];
  const opciones = [{id: "", titulo: "Sin definir"}].concat(extras.concat(valores).map((valor) => ({id: valor, titulo: valor})));
  select.innerHTML = opciones.map((opcion) => `<md-select-option value="${esc(opcion.id)}"><div slot="headline">${esc(opcion.titulo)}</div></md-select-option>`).join("");
  await select.updateComplete;
  select.value = "";
  select.value = elegido;
}
function marcarEleccion(resultado) {
  const seVa = resultado === "rechazado";
  document.querySelector("#decision-titulo").textContent = seVa ? "Se va" : "Se queda";
  document.querySelector("#decision-motivo").label = seVa ? "Por qué se va" : "Por qué se queda";
  document.querySelector("#decision-aviso").textContent = seVa ? "Si se va, escribe por qué." : "";
}
function estiloHojaDialogo() {
  const raiz = dialogo.shadowRoot;
  if (!raiz || raiz.adoptedStyleSheets.some((hoja) => hoja.__hojaDialogo)) return;
  const hoja = new CSSStyleSheet();
  hoja.__hojaDialogo = true;
  hoja.replaceSync("@media (max-width: 720px) { dialog { margin: 0 !important; inset: auto 0 0 0 !important; width: 100% !important; max-width: 100% !important; height: auto !important; max-height: calc(100% - 48px) !important; transform: none !important; } .container { width: 100% !important; max-width: 100% !important; border-radius: 28px 28px 0 0 !important; animation: hoja-subir .3s cubic-bezier(.05, .7, .1, 1); } @keyframes hoja-subir { from { transform: translateY(100%); } to { transform: translateY(0); } } } @media (max-width: 720px) and (prefers-reduced-motion: reduce) { .container { animation: none; } }");
  raiz.adoptedStyleSheets = [...raiz.adoptedStyleSheets, hoja];
}
function abrirHoja(id) {
  const item = (consulta && consulta.tipificacion || []).find((fila) => fila.id === id) || {};
  pendiente = {id, resultado: ""};
  document.querySelector("#hoja-titulo").textContent = item.sintesis || item.comentario || "";
  document.querySelector("#hoja").hidden = false;
  document.querySelector("#hoja [data-resultado='aceptado']").focus();
}
function cerrarHoja() {
  document.querySelector("#hoja").hidden = true;
}
async function elegirDesdeHoja(evento) {
  if (evento.target.closest("[data-cerrar-hoja]")) { cerrarHoja(); return; }
  const boton = evento.target.closest("[data-resultado]");
  if (!boton || !pendiente) return;
  const id = pendiente.id;
  const resultado = boton.dataset.resultado;
  cerrarHoja();
  await prepararDecision(id, resultado, "");
}
async function prepararDecision(id, resultado, motivoInicial) {
  const item = (consulta && consulta.tipificacion || []).find((fila) => fila.id === id) || {};
  pendiente = {id, resultado: resultado || ""};
  document.querySelector("#decision-sintesis").value = item.sintesis || item.comentario || "";
  await ponerOpciones(document.querySelector("#decision-modulo"), modulosOficiales, item.modulo || "");
  await ponerOpciones(document.querySelector("#decision-etiqueta"), etiquetasOficiales, item.etiqueta || "");
  document.querySelector("#decision-motivo").value = item.motivo || motivoInicial || "";
  marcarEleccion(pendiente.resultado);
  dialogo.show();
  dialogo.addEventListener("opened", () => document.querySelector("#decision-sintesis").focus(), {once: true});
}
async function abrirDecision(evento) {
  if (evento.target.closest("[data-ojo]")) return;
  const enMovil = window.matchMedia("(max-width: 720px)").matches;
  const tarjeta = enMovil && evento.target.closest("#tipificacion .tarjeta");
  const hallazgo = (tarjeta && tarjeta.querySelector("[data-abrir]")) || evento.target.closest("[data-abrir]");
  if (hallazgo && enMovil) {
    abrirHoja(hallazgo.dataset.id);
    return;
  }
  const boton = evento.target.closest("[data-resultado]");
  if (!boton || !boton.dataset.id) return;
  await prepararDecision(boton.dataset.id, boton.dataset.resultado, boton.dataset.motivo || "");
}
async function confirmarDecision(evento) {
  evento.preventDefault();
  if (!pendiente) return;
  const sintesis = document.querySelector("#decision-sintesis").value.trim();
  const modulo = document.querySelector("#decision-modulo").value;
  const etiqueta = document.querySelector("#decision-etiqueta").value;
  const motivo = document.querySelector("#decision-motivo").value.trim();
  const avisoModal = document.querySelector("#decision-aviso");
  avisoModal.textContent = "";
  if (!pendiente.resultado) {
    avisoModal.textContent = "Elige si se queda o se va.";
    return;
  }
  if (!sintesis) {
    avisoModal.textContent = "Escribe la síntesis.";
    return;
  }
  if (pendiente.resultado === "rechazado" && !motivo) {
    avisoModal.textContent = "Si se va, escribe por qué.";
    return;
  }
  const respuesta = await fetch("/api/decidir", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({mes: document.querySelector("#mes").value, id: pendiente.id, resultado: pendiente.resultado, motivo, sintesis, modulo, etiqueta})
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) { avisoModal.textContent = datos.error || "No se pudo registrar la decisión."; return; }
  dialogo.close();
  aviso.textContent = pendiente.resultado === "aceptado" ? "Se queda." : "Se va.";
  pendiente = null;
  cargar();
}
function celdaJira(item) {
  if (item.jira && item.jira.clave) return `<td class="marca"><a href="${esc(item.jira.url || "")}" target="_blank" rel="noopener">${esc(item.jira.clave)}</a></td>`;
  if (item.id) return `<td class="marca"><md-checkbox touch-target="wrapper" data-jira data-mes="${esc(item.mes)}" data-id="${esc(item.id)}" aria-label="Seleccionar para Jira"></md-checkbox></td>`;
  return `<td class="marca"></td>`;
}
function filaConOjo(celdas, item, conDecision = true) {
  const columnas = (celdas.match(/<td/g) || []).length + 1;
  return `<tr>${celdas}<td class="ojo">${botonOjo(item)}</td></tr>${filaAcordeon(item, columnas, conDecision)}`;
}
function detalleTarjeta(item, conDecision) {
  const lista = lineasHallazgo(item).map((texto) => `<li>${esc(texto)}</li>`).join("");
  const nota = conDecision ? esc(textoDecision(item)) : (item.motivo ? esc(item.motivo) : "");
  const decision = nota ? `<p>${nota}</p>` : "";
  return `<div class="detalle" hidden>${decision}<p class="origen">Hallazgos</p><ul>${lista}</ul></div>`;
}
function marcaTarjeta(item) {
  if (item.jira && item.jira.clave) return `<a class="ticket" href="${esc(item.jira.url || "")}" target="_blank" rel="noopener">${esc(item.jira.clave)}</a>`;
  if (!item.id) return "";
  return `<md-checkbox touch-target="wrapper" data-jira data-mes="${esc(item.mes)}" data-id="${esc(item.id)}" aria-label="Seleccionar para Jira"></md-checkbox>`;
}
function tarjetaLista(item, conDecision, marca) {
  const titulo = item.sintesis || item.comentario || "";
  const veces = item.conteo == null || item.conteo === "" ? "" : `<span>${item.conteo}</span>`;
  return `<article class="tarjeta"><div class="cabeza-tarjeta">${marca || ""}<p class="texto">${esc(titulo)}</p></div><div class="meta md-typescale-label-medium"><span class="luz ${esc(item.criticidad)}">${esc(item.criticidad || "sin dato")}</span>${veces}<span>${esc(item.mes || "")}</span><span>${esc(item.modulo || "Sin definir")}</span><span>${esc(item.etiqueta || "Sin definir")}</span><span class="ojo">${botonOjo()}</span></div>${detalleTarjeta(item, conDecision)}</article>`;
}
function barraTarjetas(conSeleccion) {
  const seleccion = conSeleccion ? `<label class="marcar-todos md-typescale-label-medium"><md-checkbox touch-target="wrapper" id="jira-todos-tarjetas" aria-label="Seleccionar los que se quedan"></md-checkbox>Seleccionar los que se quedan</label>` : "";
  return `<div class="ordenar-tarjetas">${seleccion}<md-text-button type="button" class="orden" data-orden="fecha">Mes${marcaOrden("fecha")}</md-text-button><md-text-button type="button" class="orden" data-orden="criticidad">Criticidad${marcaOrden("criticidad")}</md-text-button></div>`;
}
function conTarjetas(tabla, items, conDecision, marcaDe, conSeleccion) {
  const tarjetas = items.map((item) => tarjetaLista(item, conDecision, marcaDe ? marcaDe(item) : "")).join("");
  return `${tabla}<div class="tarjetas">${barraTarjetas(conSeleccion)}${tarjetas}</div>`;
}
function tablaExcluidos(items) {
  if (!items || !items.length) return "<p class=\\"vacio\\">Todavía no hay casos excluidos.</p>";
  const filas = ordenarHallazgos(items);
  const filasHtml = filas.map((item) => filaConOjo(`<td>${esc(item.mes)}</td><td>${esc(item.modulo)}</td><td>${esc(item.etiqueta || "")}</td><td><span class="luz md-typescale-label-medium ${esc(item.criticidad)}">${esc(item.criticidad || "sin dato")}</span></td><td>${esc(item.sintesis || "")}</td>`, item)).join("");
  const tabla = `<table class="listado"><thead><tr>${cabezaOrden("fecha", "Mes")}<th>Módulo</th><th>Etiqueta</th>${cabezaOrden("criticidad", "Criticidad")}<th>Síntesis</th><th class="ojo"></th></tr></thead><tbody>${filasHtml}</tbody></table>`;
  return conTarjetas(tabla, filas, true);
}
function tablaHistorico(items) {
  if (!items || !items.length) return "<p class=\\"vacio\\">Todavía no hay casos que se queden.</p>";
  const filas = ordenarHallazgos(items);
  const filasHtml = filas.map((item) => filaConOjo(`${celdaJira(item)}<td>${esc(item.mes)}</td><td>${esc(item.modulo)}</td><td>${esc(item.etiqueta)}</td><td><span class="luz md-typescale-label-medium ${esc(item.criticidad)}">${esc(item.criticidad || "sin dato")}</span></td><td>${esc(item.sintesis || "")}</td><td>${item.conteo ?? ""}</td>`, item, false)).join("");
  const tabla = `<table class="listado"><thead><tr><th class="marca"><md-checkbox touch-target="wrapper" id="jira-todos" aria-label="Seleccionar los que se quedan"></md-checkbox></th>${cabezaOrden("fecha", "Mes")}<th>Módulo</th><th>Etiqueta</th>${cabezaOrden("criticidad", "Criticidad")}<th>Síntesis</th><th>Conteo</th><th class="ojo"></th></tr></thead><tbody>${filasHtml}</tbody></table>`;
  return conTarjetas(tabla, filas, false, marcaTarjeta, true);
}
function tablaBacklog(items) {
  if (!items || !items.length) return "<p class=\\"vacio\\">Todavía no hay casos en el backlog.</p>";
  const filas = ordenarHallazgos(items);
  const filasHtml = filas.map((item) => filaConOjo(`<td class="marca">${item.jira && item.jira.clave ? `<a href="${esc(item.jira.url || "")}" target="_blank" rel="noopener">${esc(item.jira.clave)}</a>` : ""}</td><td>${esc(item.mes)}</td><td>${esc(item.modulo)}</td><td>${esc(item.etiqueta)}</td><td><span class="luz md-typescale-label-medium ${esc(item.criticidad)}">${esc(item.criticidad || "sin dato")}</span></td><td>${esc(item.sintesis || "")}</td><td>${item.conteo ?? ""}</td>`, item)).join("");
  const tabla = `<table class="listado"><thead><tr><th class="marca">Ticket</th>${cabezaOrden("fecha", "Mes")}<th>Módulo</th><th>Etiqueta</th>${cabezaOrden("criticidad", "Criticidad")}<th>Síntesis</th><th>Conteo</th><th class="ojo"></th></tr></thead><tbody>${filasHtml}</tbody></table>`;
  return conTarjetas(tabla, filas, true, (item) => item.jira && item.jira.clave ? `<a class="ticket" href="${esc(item.jira.url || "")}" target="_blank" rel="noopener">${esc(item.jira.clave)}</a>` : "");
}
function esc(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (letra) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\\"": "&quot;", "'": "&#39;" }[letra]));
}
</script>
</body>
</html>
"""
    return pagina.replace("/*MODULOS*/[]", json.dumps(list(MODULOS), ensure_ascii=False)).replace(
        "/*ETIQUETAS*/[]", json.dumps(list(ETIQUETAS), ensure_ascii=False)
    )


def servir(raiz: Path, puerto: int = 8765, abrir: bool = True) -> int:
    global _RAIZ
    _RAIZ = raiz
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Solicitud)
    if abrir:
        webbrowser.open(f"http://127.0.0.1:{puerto}/")
    print(f"Consulta en http://127.0.0.1:{puerto}/")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
    return 0


class Solicitud(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        ruta = urlparse(self.path)
        if ruta.path == "/":
            self._html(html_pagina())
            return
        if ruta.path == "/plantilla/feedback_response_2026-01.xlsx":
            self._archivo(plantilla(), "feedback_response_2026-01.xlsx")
            return
        if ruta.path == "/api/consulta":
            mes = ""
            if "?" in self.path:
                for parte in self.path.split("?", 1)[1].split("&"):
                    if parte.startswith("mes="):
                        mes = parte.split("=", 1)[1]
            self._json(_consulta(mes))
            return
        self.send_error(404)

    def do_POST(self) -> None:
        ruta = urlparse(self.path).path
        if ruta not in ("/api/guardar", "/api/decidir", "/api/jira"):
            self.send_error(404)
            return
        longitud = int(self.headers.get("Content-Length", "0"))
        crudo = self.rfile.read(longitud)
        try:
            if ruta == "/api/decidir":
                cuerpo = json.loads(crudo.decode("utf-8"))
                decidir(
                    _RAIZ,
                    str(cuerpo.get("mes") or ""),
                    str(cuerpo.get("id") or ""),
                    str(cuerpo.get("resultado") or ""),
                    str(cuerpo.get("motivo") or ""),
                    sintesis=None if "sintesis" not in cuerpo else str(cuerpo.get("sintesis") or ""),
                    modulo=None if "modulo" not in cuerpo else str(cuerpo.get("modulo") or ""),
                    etiqueta=None if "etiqueta" not in cuerpo else str(cuerpo.get("etiqueta") or ""),
                )
                self._json({"ok": True})
                return
            if ruta == "/api/jira":
                cuerpo = json.loads(crudo.decode("utf-8"))
                items = cuerpo.get("items")
                if not isinstance(items, list):
                    raise JiraInvalida("El envío no es válido.")
                self._json(enviar(_RAIZ, items))
                return
            mes = recibir_libro(_RAIZ, self.headers.get("X-Nombre", ""), crudo)
        except (CapturaInvalida, DecisionInvalida, JiraInvalida, json.JSONDecodeError, UnicodeError) as exc:
            motivo = exc.motivo if isinstance(exc, (CapturaInvalida, DecisionInvalida, JiraInvalida)) else "El envío no es válido."
            self._json({"error": motivo}, 400)
            return
        self._json({"ok": True, "mes": mes})

    def log_message(self, formato: str, *args) -> None:
        return

    def _html(self, contenido: str) -> None:
        cuerpo = contenido.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _archivo(self, contenido: bytes, nombre: str) -> None:
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.send_header("Content-Disposition", f'attachment; filename="{nombre}"')
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def _json(self, valor: dict, codigo: int = 200) -> None:
        cuerpo = json.dumps(valor, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


def _consulta(mes: str) -> dict:
    resumen = resumir(_RAIZ)
    return {
        "filas": _filas(mes),
        "por_mes": resumen["por_mes"],
        "totales": resumen["totales"],
        "historico": resumen["historico"],
        "excluidos": resumen["excluidos"],
        "backlog": resumen["backlog"],
        "tipificacion": incidentes(_RAIZ, mes),
        "meses": resumen["meses"],
    }


def _filas(mes: str) -> list[dict]:
    if not mes:
        return []
    ruta = _RAIZ / "datos" / "meses" / f"feedback_response_{mes}.xlsx"
    if not ruta.is_file():
        return []
    try:
        respuestas, _ = leer_libro(ruta, mes)
    except EntradaInvalida:
        return []
    return [
        {
            "pestana": item.pestana,
            "fecha": item.fecha.date().isoformat() if item.fecha else "",
            "csat": item.csat,
            "csat_2": item.csat_2,
            "ces": item.ces,
            "pregunta": item.pregunta_abierta,
        }
        for item in respuestas
    ]
