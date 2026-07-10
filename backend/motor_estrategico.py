import math

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def get_walkable_cells(grid_map):
    # Walkable cells are those with val == 0 (paths)
    # Grid size is 5x5, 1-indexed
    walkable = set()
    for cell in grid_map:
        if cell['val'] == 0:
            walkable.add((cell['x'], cell['y']))
    return walkable

def get_valid_moves(pos, grid_map, allow_capture=False, opponent_pos=None):
    # pos is (x, y)
    # moves: up, down, left, right
    x, y = pos
    candidates = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
    walkable = get_walkable_cells(grid_map)
    
    valid = []
    for cx, cy in candidates:
        if 1 <= cx <= 5 and 1 <= cy <= 5:
            # Must be a path (val == 0) OR the agent's current position OR opponent's position (if capture allowed)
            if (cx, cy) in walkable or (cx, cy) == pos or (allow_capture and opponent_pos and (cx, cy) == opponent_pos):
                valid.append((cx, cy))
    return valid

def evaluate_state(guardian_pos, intruder_pos, grid_map, weights):
    # V = w1 * CoberturaValor + w2 * (1 / (DistanciaIntruso + 0.1)) - w3 * EstantesComp
    w1 = weights.get('w1', 5.0)
    w2 = weights.get('w2', 15.0)
    w3 = weights.get('w3', 10.0)
    
    # 1. DistanciaIntruso
    dist_intruder = manhattan_distance(guardian_pos, intruder_pos)
    if dist_intruder == 0:
        # Intruder is caught! Highly favorable for the Guardian
        return 10000.0
    
    # 2. CoberturaValor: Sum of 1 / (dist(Guardian, Shelf) + 1) for all active shelves (val == 1)
    cobertura_valor = 0.0
    # 3. EstantesComp: Count of empty shelves (val == 10)
    estantes_comp = 0
    
    for cell in grid_map:
        val = cell['val']
        cx, cy = cell['x'], cell['y']
        if val == 1:
            dist_shelf = manhattan_distance(guardian_pos, (cx, cy))
            cobertura_valor += 1.0 / (dist_shelf + 1.0)
        elif val == 10:
            estantes_comp += 1
            
    v = w1 * cobertura_valor + w2 * (1.0 / (dist_intruder + 0.1)) - w3 * estantes_comp
    return v

def minimax(guardian_pos, intruder_pos, grid_map, depth, alpha, beta, is_max, weights, search_stats):
    search_stats['nodes_visited'] += 1
    
    # Base cases: depth 0 or intruder caught
    dist = manhattan_distance(guardian_pos, intruder_pos)
    if depth == 0 or dist == 0:
        return evaluate_state(guardian_pos, intruder_pos, grid_map, weights), None
        
    if is_max:
        # Guardian's turn (Maximizer)
        max_eval = -float('inf')
        best_move = None
        # Guardian can capture the intruder
        valid_moves = get_valid_moves(guardian_pos, grid_map, allow_capture=True, opponent_pos=intruder_pos)
        
        # Sort moves heuristically (closer to intruder first) to optimize pruning
        valid_moves.sort(key=lambda m: manhattan_distance(m, intruder_pos))
        
        for move in valid_moves:
            eval_val, _ = minimax(move, intruder_pos, grid_map, depth - 1, alpha, beta, False, weights, search_stats)
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                search_stats['prunings'] += 1
                break # Beta pruning
        return max_eval, best_move
    else:
        # Intruder's turn (Minimizer)
        min_eval = float('inf')
        best_move = None
        valid_moves = get_valid_moves(intruder_pos, grid_map, allow_capture=False)
        
        # Sort moves heuristically (further from guardian first) to optimize pruning
        valid_moves.sort(key=lambda m: manhattan_distance(m, guardian_pos), reverse=True)
        
        for move in valid_moves:
            eval_val, _ = minimax(guardian_pos, move, grid_map, depth - 1, alpha, beta, True, weights, search_stats)
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
            beta = min(beta, eval_val)
            if beta <= alpha:
                search_stats['prunings'] += 1
                break # Alpha pruning
        return min_eval, best_move

def find_best_move_guardian(guardian_pos, intruder_pos, grid_map, weights=None):
    if weights is None:
        weights = {'w1': 5.0, 'w2': 15.0, 'w3': 10.0}
    
    search_stats = {'nodes_visited': 0, 'prunings': 0}
    eval_val, move = minimax(
        guardian_pos, 
        intruder_pos, 
        grid_map, 
        depth=4, 
        alpha=-float('inf'), 
        beta=float('inf'), 
        is_max=True, 
        weights=weights, 
        search_stats=search_stats
    )
    
    # If no move selected (no valid moves), stay in place
    if move is None:
        move = guardian_pos
        
    return {
        'best_move': move,
        'eval_value': eval_val,
        'nodes_visited': search_stats['nodes_visited'],
        'prunings': search_stats['prunings']
    }

def find_best_move_intruder(guardian_pos, intruder_pos, grid_map):
    # Intruder's behavior in the simulation:
    # 1. If adjacent to a full shelf (val == 1), it can stay and rob it (robbery action is handled in main loop)
    # 2. Otherwise, it moves to an adjacent cell that:
    #    - Avoids the Guardian (maximizes distance)
    #    - Gets closer to the nearest full shelf (val == 1)
    # We will simulate this using a simple evaluation from the intruder's perspective:
    # U = 3.0 * dist_guardian - 1.5 * dist_nearest_shelf
    valid_moves = get_valid_moves(intruder_pos, grid_map, allow_capture=False)
    if not valid_moves:
        return intruder_pos
        
    # Find full shelves
    full_shelves = []
    for cell in grid_map:
        if cell['val'] == 1:
            full_shelves.append((cell['x'], cell['y']))
            
    best_move = intruder_pos
    max_utility = -float('inf')
    
    for move in valid_moves:
        dist_g = manhattan_distance(move, guardian_pos)
        
        # Avoid getting caught immediately (dist_g == 0 is fatal unless guardian is already there, but intruder cannot move into guardian)
        if move == guardian_pos:
            continue
            
        if full_shelves:
            dist_s = min(manhattan_distance(move, s) for s in full_shelves)
        else:
            dist_s = 0
            
        # Utility formula for intruder
        utility = 3.0 * dist_g - 1.5 * dist_s
        
        # Small random factor to avoid deterministic loops
        # utility += (hash(move) % 10) * 0.1
        
        if utility > max_utility:
            max_utility = utility
            best_move = move
            
    return best_move
