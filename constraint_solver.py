import math

def distance_sq(p1, p2):
    return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2

def length(p1, p2):
    return math.sqrt(distance_sq(p1, p2))

def normalize(v):
    l = math.sqrt(v[0]**2 + v[1]**2)
    if l < 1e-6: return (0, 0), 0
    return (v[0]/l, v[1]/l), l

def get_point(walls, ref):
    # ref is (wall_index, endpoint_index 0=start 1=end)
    w = walls[ref[0]]
    return list(w['start']) if ref[1] == 0 else list(w['end'])

def set_point(walls, ref, pos):
    w = walls[ref[0]]
    if ref[1] == 0: w['start'] = tuple(pos)
    else: w['end'] = tuple(pos)

def get_inv_mass(walls, ref):
    """Returns 0.0 if point is anchored, 1.0 otherwise."""
    w = walls[ref[0]]
    # Check if 'anchored' list exists, default to False if not
    anchors = w.get('anchored', [False, False])
    if anchors[ref[1]]: return 0.0
    return 1.0

def apply_rotation(walls, w_idx, target_angle, anchors, stiffness=1.0):
    w = walls[w_idx]
    curr_len = length(w['start'], w['end'])
    dx = w['end'][0] - w['start'][0]
    dy = w['end'][1] - w['start'][1]
    curr_angle = math.atan2(dy, dx)
    
    # Interpolate angle for stiffness (Shortest path interpolation)
    diff = target_angle - curr_angle
    while diff > math.pi: diff -= 2*math.pi
    while diff < -math.pi: diff += 2*math.pi
    
    final_angle = curr_angle + diff * stiffness
    
    # Determine Pivot
    if anchors[0]: pivot = w['start']
    elif anchors[1]: pivot = w['end']
    else: pivot = ((w['start'][0]+w['end'][0])/2, (w['start'][1]+w['end'][1])/2)
    
    c = math.cos(final_angle)
    s = math.sin(final_angle)
    
    # Re-calculate points based on pivot
    if pivot == w['start']:
        new_end = (pivot[0] + c*curr_len, pivot[1] + s*curr_len)
        set_point(walls, (w_idx, 1), new_end)
    elif pivot == w['end']:
        new_start = (pivot[0] - c*curr_len, pivot[1] - s*curr_len)
        set_point(walls, (w_idx, 0), new_start)
    else:
        half = curr_len / 2.0
        set_point(walls, (w_idx, 0), (pivot[0] - c*half, pivot[1] - s*half))
        set_point(walls, (w_idx, 1), (pivot[0] + c*half, pivot[1] + s*half))

def solve_constraints(walls, constraints, iterations=10):
    """
    Iteratively solves geometric constraints by modifying wall coordinates in place.
    Respects 'anchored' flags on wall endpoints.
    """
    num_walls = len(walls)
    
    for _ in range(iterations):
        for c in constraints:
            # --- SAFETY CHECK ---
            valid = True
            for idx in c['indices']:
                w_idx = idx[0] if isinstance(idx, (list, tuple)) else idx
                if w_idx < 0 or w_idx >= num_walls:
                    valid = False; break
            if not valid: continue

            ctype = c['type']
            
            # --- COINCIDENT (Point-Point) ---
            if ctype == 'COINCIDENT':
                refs = c['indices'] # [(w1, p1), (w2, p2)]
                pts = [get_point(walls, r) for r in refs]
                if not pts: continue
                
                ws = [get_inv_mass(walls, r) for r in refs]
                w_sum = sum(ws)
                if w_sum == 0: continue # Both anchored, cannot satisfy
                
                # Weighted Average
                avg_x = sum(p[0] * w for p, w in zip(pts, ws)) / w_sum
                avg_y = sum(p[1] * w for p, w in zip(pts, ws)) / w_sum
                target = (avg_x, avg_y)

                # Special case: If exactly one is anchored, snap strictly to it 
                # (The weighted average handles this mathematically, 
                # but floating point error might introduce drift, so we force it).
                for i, w in enumerate(ws):
                    if w == 0:
                        target = pts[i]
                        break
                
                for i, r in enumerate(refs):
                    if ws[i] > 0:
                        set_point(walls, r, target)

            # --- FIXED LENGTH ---
            elif ctype == 'LENGTH':
                w_idx = c['indices'][0]
                target_len = c['value']
                p1 = list(walls[w_idx]['start'])
                p2 = list(walls[w_idx]['end'])
                
                w1 = get_inv_mass(walls, (w_idx, 0))
                w2 = get_inv_mass(walls, (w_idx, 1))
                if w1 + w2 == 0: continue

                curr_vec = (p2[0]-p1[0], p2[1]-p1[1])
                dir_vec, curr_len = normalize(curr_vec)
                if curr_len == 0: continue
                
                diff = curr_len - target_len
                
                # Distribute correction
                f1 = w1 / (w1 + w2)
                f2 = w2 / (w1 + w2)
                
                move_x = dir_vec[0] * diff
                move_y = dir_vec[1] * diff
                
                set_point(walls, (w_idx, 0), (p1[0] + move_x * f1, p1[1] + move_y * f1))
                set_point(walls, (w_idx, 1), (p2[0] - move_x * f2, p2[1] - move_y * f2))

            # --- EQUAL LENGTH (Improved Stability) ---
            elif ctype == 'EQUAL':
                w1_idx, w2_idx = c['indices']
                # Calculate current lengths
                l1 = length(walls[w1_idx]['start'], walls[w1_idx]['end'])
                l2 = length(walls[w2_idx]['start'], walls[w2_idx]['end'])
                
                # Check "mass" of the walls (are they anchored?)
                # We approximate wall mass by summing endpoint inv_masses
                inv_m1 = get_inv_mass(walls, (w1_idx, 0)) + get_inv_mass(walls, (w1_idx, 1))
                inv_m2 = get_inv_mass(walls, (w2_idx, 0)) + get_inv_mass(walls, (w2_idx, 1))
                
                if inv_m1 + inv_m2 == 0: continue
                
                # Weighted average target length
                # If Wall 1 is fully anchored (inv_m1=0), target becomes l1.
                target_len = (l1 * inv_m2 + l2 * inv_m1) / (inv_m1 + inv_m2)
                
                # Apply LENGTH constraint logic to both
                for idx, curr_l in [(w1_idx, l1), (w2_idx, l2)]:
                    if curr_l == 0: continue
                    factor = (curr_l - target_len) / curr_l
                    
                    p1 = list(walls[idx]['start'])
                    p2 = list(walls[idx]['end'])
                    m1 = get_inv_mass(walls, (idx, 0))
                    m2 = get_inv_mass(walls, (idx, 1))
                    
                    if m1 + m2 == 0: continue

                    # Correct positions to match target_len
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    
                    # Move p1
                    c1 = m1 / (m1 + m2) * factor
                    set_point(walls, (idx, 0), (p1[0] + dx * c1, p1[1] + dy * c1))
                    
                    # Move p2
                    c2 = m2 / (m1 + m2) * factor
                    set_point(walls, (idx, 1), (p2[0] - dx * c2, p2[1] - dy * c2))

            # --- ANGLE HELPERS (Improved Anchoring Support) ---
            elif ctype in ['PARALLEL', 'PERPENDICULAR']:
                w1_idx, w2_idx = c['indices']
                w1 = walls[w1_idx]
                w2 = walls[w2_idx]
                
                # Check anchors
                anchors1 = w1.get('anchored', [False, False])
                anchors2 = w2.get('anchored', [False, False])
                
                # If a wall has ANY anchored point, we treat it as the master rotation reference
                w1_fixed = anchors1[0] or anchors1[1]
                w2_fixed = anchors2[0] or anchors2[1]
                
                dx1, dy1 = w1['end'][0] - w1['start'][0], w1['end'][1] - w1['start'][1]
                dx2, dy2 = w2['end'][0] - w2['start'][0], w2['end'][1] - w2['start'][1]
                a1 = math.atan2(dy1, dx1)
                a2 = math.atan2(dy2, dx2)
                
                target_a1, target_a2 = a1, a2
                
                if ctype == 'PARALLEL':
                    if abs(a1 - a2) > math.pi/2:
                        if a2 < a1: a2 += math.pi 
                        else: a2 -= math.pi
                    avg = (a1 + a2) / 2.0
                    target_a1, target_a2 = avg, avg
                elif ctype == 'PERPENDICULAR':
                    diff = a2 - a1
                    while diff > math.pi: diff -= 2*math.pi
                    while diff < -math.pi: diff += 2*math.pi
                    goal = math.pi/2 if diff > 0 else -math.pi/2
                    correction = (goal - diff) / 2.0
                    target_a1 = a1 - correction
                    target_a2 = a2 + correction

                # Prioritize fixed walls
                if w1_fixed and not w2_fixed:
                    target_a1 = a1 # Don't move 1
                    target_a2 = a1 if ctype == 'PARALLEL' else a1 + (math.pi/2 * (1 if a2>a1 else -1))
                elif w2_fixed and not w1_fixed:
                    target_a2 = a2 # Don't move 2
                    target_a1 = a2 if ctype == 'PARALLEL' else a2 - (math.pi/2 * (1 if a2>a1 else -1))
                
                # Apply Rotations with stiffness
                stiffness = 0.5 
                
                # Only apply if not fully anchored (both points)
                if not (anchors1[0] and anchors1[1]):
                    apply_rotation(walls, w1_idx, target_a1, anchors1, stiffness)
                if not (anchors2[0] and anchors2[1]):
                    apply_rotation(walls, w2_idx, target_a2, anchors2, stiffness)

            # --- HORIZONTAL / VERTICAL ---
            elif ctype == 'HORIZONTAL' or ctype == 'VERTICAL':
                w_idx = c['indices'][0]
                w1 = get_inv_mass(walls, (w_idx, 0))
                w2 = get_inv_mass(walls, (w_idx, 1))
                if w1 + w2 == 0: continue
                
                w = walls[w_idx]
                if ctype == 'HORIZONTAL':
                    avg_y = (w['start'][1] + w['end'][1]) / 2.0
                    # If one is anchored, snap to that Y
                    if w1 == 0: avg_y = w['start'][1]
                    elif w2 == 0: avg_y = w['end'][1]
                    
                    if w1 > 0: set_point(walls, (w_idx, 0), (w['start'][0], avg_y))
                    if w2 > 0: set_point(walls, (w_idx, 1), (w['end'][0], avg_y))
                else:
                    avg_x = (w['start'][0] + w['end'][0]) / 2.0
                    if w1 == 0: avg_x = w['start'][0]
                    elif w2 == 0: avg_x = w['end'][0]
                    
                    if w1 > 0: set_point(walls, (w_idx, 0), (avg_x, w['start'][1]))
                    if w2 > 0: set_point(walls, (w_idx, 1), (avg_x, w['end'][1]))