:- use_module(library(http/thread_httpd)).
:- use_module(library(http/http_dispatch)).
:- use_module(library(http/http_json)).
:- use_module(library(http/http_parameters)).
:- use_module(library(http/http_client)).

% Dynamic Facts
:- dynamic celda/3.             % celda(X, Y, Tipo)
:- dynamic estante_producto/4.   % estante_producto(EstanteId, Producto, Cantidad, CapacidadMax)
:- dynamic estante_posicion/3.   % estante_posicion(EstanteId, X, Y)
:- dynamic camara/4.             % camara(Id, X, Y, Estado)
:- dynamic alarma/2.             % alarma(Tipo, Estado)

% Threat Evaluation Rules
evaluar_amenaza(intruso, _, _, critico, [alerta_intrusion, intruso_detectado]).
evaluar_amenaza(empleado, _, _, ninguno, [personal_autorizado]).
evaluar_amenaza(cliente, restringida, noche, alto, [cliente_en_zona_restringida, horario_no_permitido]).
evaluar_amenaza(cliente, restringida, dia, medio, [cliente_en_zona_restringida]).
evaluar_amenaza(cliente, publica, _, ninguno, [cliente_en_zona_publica]).
evaluar_amenaza(objeto_desconocido, restringida, _, alto, [objeto_no_identificado, zona_restringida]).
evaluar_amenaza(objeto_desconocido, publica, _, bajo, [objeto_no_identificado]).
evaluar_amenaza(_, _, _, bajo, [evento_indeterminado]).

% Replenishment Rules
requiere_reabastecimiento(EstanteId, Producto, Cantidad, CapacidadMax) :-
    estante_producto(EstanteId, Producto, Cantidad, CapacidadMax),
    (Cantidad / CapacidadMax) =< 0.20.

% Initialize database with default configuration
init_db :-
    retractall(celda(_, _, _)),
    retractall(estante_producto(_, _, _, _)),
    retractall(estante_posicion(_, _, _)),
    retractall(camara(_, _, _, _)),
    retractall(alarma(_, _)),
    
    % Default Grid 5x5:
    % Row 1
    assertz(celda(1, 1, 1)), assertz(estante_posicion(estante_1, 1, 1)),
    assertz(celda(2, 1, 0)),
    assertz(celda(3, 1, 1)), assertz(estante_posicion(estante_2, 3, 1)),
    assertz(celda(4, 1, 0)),
    assertz(celda(5, 1, 1)), assertz(estante_posicion(estante_3, 5, 1)),
    
    % Row 2
    assertz(celda(1, 2, 0)),
    assertz(celda(2, 2, 0)),
    assertz(celda(3, 2, 0)),
    assertz(celda(4, 2, 0)),
    assertz(celda(5, 2, 0)),
    
    % Row 3
    assertz(celda(1, 3, 1)), assertz(estante_posicion(estante_4, 1, 3)),
    assertz(celda(2, 3, 0)),
    assertz(celda(3, 3, 1)), assertz(estante_posicion(estante_5, 3, 3)),
    assertz(celda(4, 3, 0)),
    assertz(celda(5, 3, 1)), assertz(estante_posicion(estante_6, 5, 3)),
    
    % Row 4
    assertz(celda(1, 4, 0)),
    assertz(celda(2, 4, 0)),
    assertz(celda(3, 4, 0)),
    assertz(celda(4, 4, 0)),
    assertz(celda(5, 4, 0)),
    
    % Row 5
    assertz(celda(1, 5, 1)), assertz(estante_posicion(estante_7, 1, 5)),
    assertz(celda(2, 5, 0)),
    assertz(celda(3, 5, 0)),
    assertz(celda(4, 5, 0)),
    assertz(celda(5, 5, 1)), assertz(estante_posicion(estante_8, 5, 5)),

    % Default stocks (Max Cap = 10 for all)
    assertz(estante_producto(estante_1, "Arroz", 10, 10)),
    assertz(estante_producto(estante_2, "Azucar", 8, 10)),
    assertz(estante_producto(estante_3, "Fideos", 10, 10)),
    assertz(estante_producto(estante_4, "Leche", 5, 10)),
    assertz(estante_producto(estante_5, "Aceite", 10, 10)),
    assertz(estante_producto(estante_6, "Cafe", 9, 10)),
    assertz(estante_producto(estante_7, "Atun", 7, 10)),
    assertz(estante_producto(estante_8, "Lentejas", 10, 10)),

    % Default cameras
    assertz(camara(camara_1, 2, 2, activa)),
    assertz(camara(camara_2, 4, 2, activa)),
    assertz(camara(camara_3, 2, 4, activa)),
    assertz(camara(camara_4, 4, 4, activa)),

    % Default alarms
    assertz(alarma(intrusion, inactiva)),
    assertz(alarma(reabastecimiento, inactiva)).

% Register HTTP Handlers
:- http_handler(root(state), handle_state, []).
:- http_handler(root(update_grid), handle_update_grid, []).
:- http_handler(root(update_stock), handle_update_stock, []).
:- http_handler(root(check_event_threat), handle_check_event_threat, []).
:- http_handler(root(replenishment_list), handle_replenishment_list, []).

% Handler implementations
handle_state(_Request) :-
    findall(json([x=X, y=Y, val=V]), celda(X, Y, V), Celdas),
    findall(json([estante_id=Id, producto=Prod, cantidad=Cant, max_cap=Max]), estante_producto(Id, Prod, Cant, Max), Stock),
    findall(json([id=CamId, x=CamX, y=CamY, estado=CamEst]), camara(CamId, CamX, CamY, CamEst), Camaras),
    findall(json([tipo=AlTipo, estado=AlEst]), alarma(AlTipo, AlEst), Alarmas),
    reply_json(json([celdas=Celdas, stock=Stock, camaras=Camaras, alarmas=Alarmas])).

handle_update_grid(Request) :-
    http_read_json_dict(Request, Dict),
    X = Dict.get(x),
    Y = Dict.get(y),
    Val = Dict.get(val),
    retractall(celda(X, Y, _)),
    assertz(celda(X, Y, Val)),
    % If updating the cell affects alarms, check if there is an intruder or stockout
    evaluar_alarmas_globales,
    reply_json(json([status=success, message="Grid cell updated"])).

handle_update_stock(Request) :-
    http_read_json_dict(Request, Dict),
    EstanteIdAtom = Dict.get(estante_id),
    % convert string to atom if necessary
    atom_string(EstanteId, EstanteIdAtom),
    Cantidad = Dict.get(cantidad),
    (   estante_producto(EstanteId, Producto, _, Max)
    ->  retractall(estante_producto(EstanteId, _, _, _)),
        assertz(estante_producto(EstanteId, Producto, Cantidad, Max)),
        % Update cell representation: empty if Cantidad/Max <= 0.20
        (   (Cantidad / Max) =< 0.20
        ->  NewCellVal = 10
        ;   NewCellVal = 1
        ),
        (   estante_posicion(EstanteId, X, Y)
        ->  retractall(celda(X, Y, _)),
            assertz(celda(X, Y, NewCellVal))
        ;   true
        ),
        evaluar_alarmas_globales,
        reply_json(json([status=success, message="Stock and cell updated"]))
    ;   reply_json(json([status=error, message="Estante not found"]), [status(404)])
    ).

handle_check_event_threat(Request) :-
    http_read_json_dict(Request, Dict),
    ClaseAtom = Dict.get(clase), atom_string(Clase, ClaseAtom),
    ZonaAtom = Dict.get(zona), atom_string(Zona, ZonaAtom),
    HorarioAtom = Dict.get(horario), atom_string(Horario, HorarioAtom),
    evaluar_amenaza(Clase, Zona, Horario, Nivel, CadenaInferencia),
    reply_json(json([nivel=Nivel, cadena_inferencia=CadenaInferencia])).

handle_replenishment_list(_Request) :-
    findall(
        json([estante_id=Id, producto=Prod, cantidad=Cant, max_cap=Max]),
        requiere_reabastecimiento(Id, Prod, Cant, Max),
        List
    ),
    reply_json(List).

% Helper to update global alarms status based on current facts database
evaluar_alarmas_globales :-
    % Intrusion alarm active if an intruder (value 3) is present in any cell
    (   celda(_, _, 3)
    ->  retractall(alarma(intrusion, _)), assertz(alarma(intrusion, activa))
    ;   retractall(alarma(intrusion, _)), assertz(alarma(intrusion, inactiva))
    ),
    % Replenishment alarm active if any shelf has stockout (value 10)
    (   celda(_, _, 10)
    ->  retractall(alarma(reabastecimiento, _)), assertz(alarma(reabastecimiento, activa))
    ;   retractall(alarma(reabastecimiento, _)), assertz(alarma(reabastecimiento, inactiva))
    ).

% Server entrypoint
server(Port) :-
    init_db,
    evaluar_alarmas_globales,
    http_server(http_dispatch, [port(Port)]),
    thread_get_message(_).
