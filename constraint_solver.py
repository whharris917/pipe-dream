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
                
                # Calculate weighted average center
                # Ideally, we want to move them to a common point. 
                # The point is Current_Center + Correction.
                # Simple average logic:
                # center = sum(p * w) / sum(w) ?? No, that weights positions.
                # PBD approach: C(p1, p2) = p1 - p2 = 0
                # We simply move them to their standard average, weighted by mass.
                
                # Current Gap vector
                avg_x = sum(p[0] for p in pts) / len(pts)
                avg_y = sum(p[1] for p in pts) / len(pts)
                target = (avg_x, avg_y)
                
                # If weights differ (one anchored), move strictly to the anchored one
                if ws[0] == 0 and ws[1] > 0: target = pts[0]
                elif ws[1] == 0 and ws[0] > 0: target = pts[1]
                
                # Apply
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
                # dx1 = + w1/(w1+w2) * diff * dir
                # dx2 = - w2/(w1+w2) * diff * dir
                f1 = w1 / (w1 + w2)
                f2 = w2 / (w1 + w2)
                
                move_x = dir_vec[0] * diff
                move_y = dir_vec[1] * diff
                
                set_point(walls, (w_idx, 0), (p1[0] + move_x * f1, p1[1] + move_y * f1))
                set_point(walls, (w_idx, 1), (p2[0] - move_x * f2, p2[1] - move_y * f2))

            # --- EQUAL LENGTH ---
            elif ctype == 'EQUAL':
                # Similar logic, just simpler weighting for now
                # Ideally we solve the system, but here we just average them
                w1_idx = c['indices'][0]; w2_idx = c['indices'][1]
                l1 = length(walls[w1_idx]['start'], walls[w1_idx]['end'])
                l2 = length(walls[w2_idx]['start'], walls[w2_idx]['end'])
                avg_len = (l1 + l2) / 2.0
                
                # Apply as two length constraints targeting avg_len
                # This is a simplification; strictly PBD would couple them directly.
                for idx, clen in [(w1_idx, l1), (w2_idx, l2)]:
                    p1 = list(walls[idx]['start']); p2 = list(walls[idx]['end'])
                    m1 = get_inv_mass(walls, (idx, 0)); m2 = get_inv_mass(walls, (idx, 1))
                    if m1 + m2 == 0: continue
                    
                    v, d = normalize((p2[0]-p1[0], p2[1]-p1[1]))
                    diff = d - avg_len
                    f1 = m1/(m1+m2); f2 = m2/(m1+m2)
                    
                    set_point(walls, (idx, 0), (p1[0] + v[0]*diff*f1, p1[1] + v[1]*diff*f1))
                    set_point(walls, (idx, 1), (p2[0] - v[0]*diff*f2, p2[1] - v[1]*diff*f2))

            # --- ANGLE HELPERS ---
            elif ctype in ['PARALLEL', 'PERPENDICULAR']:
                w1 = walls[c['indices'][0]]
                w2 = walls[c['indices'][1]]
                
                # Check rigidity (rotation locks)
                # If both points of a wall are anchored, that wall cannot rotate.
                anchors1 = w1.get('anchored', [False, False])
                anchors2 = w2.get('anchored', [False, False])
                fixed1 = anchors1[0] and anchors1[1]
                fixed2 = anchors2[0] and anchors2[1]
                
                if fixed1 and fixed2: continue # Cannot satisfy
                
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
                    # If one is fixed, the other aligns to it
                    if fixed1: target_a2 = a1
                    elif fixed2: target_a1 = a2
                    
                elif ctype == 'PERPENDICULAR':
                    diff = a2 - a1
                    while diff > math.pi: diff -= 2*math.pi
                    while diff < -math.pi: diff += 2*math.pi
                    
                    goal = math.pi/2 if diff > 0 else -math.pi/2
                    correction = (goal - diff) / 2.0
                    
                    target_a1 = a1 - correction
                    target_a2 = a2 + correction
                    
                    if fixed1: target_a2 = a1 + goal
                    elif fixed2: target_a1 = a2 - goal

                # Apply Rotations
                # Helper to apply rotation to a wall given a target angle
                for w_idx, target_angle, fixed, anchors in [(c['indices'][0], target_a1, fixed1, anchors1), 
                                                            (c['indices'][1], target_a2, fixed2, anchors2)]:
                    if fixed: continue
                    
                    cw = walls[w_idx]
                    curr_len = length(cw['start'], cw['end'])
                    
                    # Determine Pivot
                    if anchors[0]: pivot = cw['start']
                    elif anchors[1]: pivot = cw['end']
                    else: pivot = ((cw['start'][0]+cw['end'][0])/2, (cw['start'][1]+cw['end'][1])/2)
                    
                    # If rotating around start
                    if pivot == cw['start']:
                        new_end_x = pivot[0] + math.cos(target_angle) * curr_len
                        new_end_y = pivot[1] + math.sin(target_angle) * curr_len
                        set_point(walls, (w_idx, 1), (new_end_x, new_end_y))
                    # If rotating around end
                    elif pivot == cw['end']:
                        new_start_x = pivot[0] - math.cos(target_angle) * curr_len
                        new_start_y = pivot[1] - math.sin(target_angle) * curr_len
                        set_point(walls, (w_idx, 0), (new_start_x, new_start_y))
                    # Around Center
                    else:
                        half_l = curr_len / 2.0
                        cx, cy = pivot
                        set_point(walls, (w_idx, 0), (cx - math.cos(target_angle)*half_l, cy - math.sin(target_angle)*half_l))
                        set_point(walls, (w_idx, 1), (cx + math.cos(target_angle)*half_l, cy + math.sin(target_angle)*half_l))

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