# Contrato: avisos

`salidas/YYYY-MM/aviso.md` se escribe cuando la corrida no puede dejar un reporte oficial. Si el reporte sí queda oficial, este archivo no es necesario.

## Formato

```text
Asunto: [tipo] Ciclo YYYY-MM
Para: Líder UX
Emitido: YYYY-MM-DD HH:MM

Cuerpo en prosa, con el motivo y la ruta del archivo de entrada.
```

## Tipos

| Tipo | Cuándo | Código de `correr` |
|------|--------|--------------------|
| entrada_invalida | Falta el libro, falta una pestaña obligatoria o ninguna fecha pertenece al mes | 2 |
| salida_invalida | Dos intentos sin tabla válida, sin taxonomía válida o sin auditoría completa | 3 |
| tope_tiempo | La duración llega a 180 segundos | 3 |
| tope_costo | El costo estimado llega a 3 USD antes de clasificar todas las quejas | 3 |
| apagado | Existe `datos/control/apagado.flag` | 3 |

La criticidad no genera un aviso. El color lo fija el conteo y nadie lo corrige. La puerta de tickets permanece cerrada de todos modos en este corte.

## Correo

Con `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` y `SMTP_TO` definidas, el mismo asunto y cuerpo se envían a `SMTP_TO`. El envío fallido no borra `aviso.md`. Queda anotado al final del archivo como `Correo: no enviado`. Un envío correcto se anota como `Correo: enviado`.
