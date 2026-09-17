# StickFight

**Sandbox platformer-brawler** de stickmans articulados con estética Fancy Pants (papel beige +
sombras de hojas, terreno azul-piedra a tinta con rayones, personajes de tinta con pantalón naranja).
Recorrés un nivel con plataformas flotantes bajando enemigos a piñas hasta llegar a la SALIDA;
si te bajan, respawneás al inicio (los enemigos ya bajados quedan bajados). **Web-only** (como
DonkeyKong/Pacman): no hay `.py`, todo vive en [StickFightWeb/index.html](StickFightWeb/index.html).
Registrado en el Arcade (`landscape`).

> Ojo: nació como fighter 1v1 estilo MK (2026-07-22) y Franco lo pivoteó a sandbox (2026-07-23).
> La cámara sigue SOLO al jugador (`CFG.cam.frac` = alto del muñeco / pantalla ≈ 0.16, escala FPA);
> los enemigos son N instancias de `Fighter` con un cerebro (`newBrain()`) y radio de aggro c/histéresis.

## Arquitectura (lo no-obvio)

- **Split lógica/render.** Cada peleador tiene DOS esqueletos de 13 puntos:
  - `logicPts` = FK de `targetPose` (los keytracks nominales de los golpes) → **hitboxes**. Determinista:
    los resortes jamás alteran el frame-data.
  - `renderPts` = FK de `poseCur` (resortes críticamente amortiguados por articulación) + IK de piernas +
    mezcla de ragdoll → **dibujo y hurtboxes** (esquivar moviéndose esquiva de verdad).
- **Pose en 3 capas** (`buildPose`): (a) locomoción base computada del movimiento (lean por
  aceleración + lean por velocidad, poses de aire por vy — ley Fancy Pants: la animación se CALCULA,
  no se reproduce); (b) keytrack del ataque, overwrite enmascarado con peso; (c) aditivas (flinch,
  squash de aterrizaje, respiración).
- **Ciclo de marcha procedural** (`strideParams` + rama `gait` de `feetIK`, tuneable en `CFG.gait`):
  cada pierna alterna APOYO (el pie queda CLAVADO en el mundo — la fase avanza por distancia con
  ciclo = `2·half/duty`, así la derivada del pie en apoyo es exactamente 0 → cero patinaje) y VUELO
  (arco `sin(π·u)` con rodilla adelante vía IK). Zancada/duty/altura escalan con la velocidad.
  Antes había un sistema de "replantado por estiramiento" que parecía patas de araña — no volver a eso.
  `feetIK` corre TAMBIÉN con dt=0 (freeze de hitstop): si no, las piernas saltan a la pose FK cruda.
- **La tabla de semividas de resortes es el dial de "sueltitud"** (`CFG.spr`): el limb que golpea baja
  a `hStrike=0.02 s` durante los frames activos (converge al frame-data justo cuando pega); cabeza y
  mano libre van 1.4× más lentas (follow-through gratis).
- **11 DOF** en `Float64Array` (orden en `J`), autorados mirando a la DERECHA; `facing` espeja en FK.
  Convención: cadenas "cuelgan" (0 = abajo, dirDown), torso apunta arriba. Rodillas: flexión = valores
  NEGATIVOS de `lLl/lRl`.
- **Gotcha de `ik2(bendDir)`**: con el y-abajo del canvas, rotar +θ es HORARIO visual → para que la
  rodilla apunte hacia adelante hay que pasar `-facing` (las piernas de `feetIK` ya lo hacen).
  Pasar `facing` da piernas de pájaro — ya pasó y Franco lo notó al toque.
- **Root motion de golpes/dash**: `lungeVel()` devuelve VELOCIDAD instantánea — se suma en la
  integración (`x += (vx + rootVx)·dt`), **nunca** `vx +=` (acumularía y sale volando; ya pasó).
- **Ragdoll verlet** (13 partículas, constraints con rest tomado al activar) sólo en KNOCKDOWN/KO;
  el piso proyecta con offset de reposo POR PARTE (cabeza sobre su radio) — sin eso el cuerpo queda chato.
- **Hitstop por entidad**: `hitstopT` congela el `simDt` del par; el knockback queda `pendKb` y se
  aplica al DESCONGELAR.
- **IA con percepción honesta**: lee snapshots de hace `reactionMs` (nunca el estado actual);
  arquetipos como filas de datos (`ARCHS`); la dificultad SÓLO escala reacción/bloqueo/drop de combos.
- `separateBodies`: clinch mínimo 0.24·CH — más corto que lo usual porque el uppercut llega apenas
  0.17·CH adelante; si lo agrandás, el uppercut del combo P,P,P deja de conectar.
- **Estilo**: paleta en `PAPER/ROCK/INK` (p07). El fondo son DOS bakes world-space horneados una vez:
  `bgCanvas` (sombras de hojas, parallax 0.45) y `terrainCanvas` (roca+tinta+rayones+puerta SALIDA,
  parallax 1). Nada aditivo en efectos: sobre papel claro el composite 'lighter' se lava a blanco.
- El tope de velocidad NO es drag-vs-accel: se acelera sólo por debajo de `maxRun` (con drag suave
  encima para la embalada del dash). Con drag débil el equilibrio quedaba 65% arriba del tope.

## QA headless (sin node)

Chrome headless + `--virtual-time-budget` NO dispara rAF de forma sostenida: **la sim queda congelada
aunque los timers corran**. El loop está preparado para bombearse a mano:

- `loop(t)` es global y `scheduleRaf()` tiene dedupe → un driver inyectado puede llamar
  `loop(qaNow += 16.7)` desde un `setInterval` sin duplicar la cadena rAF.
- Handle de debug: `window.SF = {P1, P2, CFG, game, cam, MOVES, POSES, ST, simT}`; `SF.simT` es el
  reloj de simulación acumulado — agendá acciones de test por `simT`, no por tiempo real.
- `dbgFreeze = true` congela la sim (sigue dibujando) → screenshot exacto del instante deseado.
- Patrón completo (cazador de errores + driver por escenario + status dump): el harness `qa.py` de la
  sesión 2026-07-22/23; escenarios útiles: menu/fight/run/skid/jump/jab/combo/kick/ko/hang/boxes.
- Teclas de debug en vivo: `T` panel de tuning (sliders sobre `CFG`), `H` hit/hurtboxes, `G` cámara
  lenta, `Y` dump de pose a consola; triple-tap en la versión del menú abre el panel en mobile.

## Gotchas

- Todo el DOM del juego está declarado ANTES del script principal (gotcha TankWARSWeb); el script de
  cola (info/FPS/mute) va después de `arcade-shell.js`.
- El trío de context-loss invalida `bgCanvas`, `skyGrad` y `_glowCache` — si agregás un bake nuevo,
  sumalo ahí (los sprites de chispas guardan la ref en la partícula: se regeneran vía cache Map).
- Los tiempos de los keytracks (`poses[].at`) son ABSOLUTOS dentro del move y el sampler arranca
  desde `atkPose0` (la pose real al iniciar el golpe) — una pose parcial sin una clave "sostiene" el
  último valor definido.
