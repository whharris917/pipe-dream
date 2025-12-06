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

def solve_constraints(walls, constraints, iterations=10):
    """
    Iteratively solves geometric constraints by modifying wall coordinates in place.
    """
    for _ in range(iterations):
        for c in constraints:
            ctype = c['type']
            
            # --- COINCIDENT (Point-Point) ---
            if ctype == 'COINCIDENT':
                # Targets: [(w1, p1), (w2, p2)]
                # Move both points to their average position
                refs = c['indices']
                pts = [get_point(walls, r) for r in refs]
                
                # Calculate centroid
                avg_x = sum(p[0] for p in pts) / len(pts)
                avg_y = sum(p[1] for p in pts) / len(pts)
                
                # Apply
                for r in refs:
                    set_point(walls, r, (avg_x, avg_y))

            # --- FIXED LENGTH ---
            elif ctype == 'LENGTH':
                # Targets: [w_idx] (Implies both points of the wall)
                w_idx = c['indices'][0]
                target_len = c['value']
                
                p1 = list(walls[w_idx]['start'])
                p2 = list(walls[w_idx]['end'])
                
                curr_vec = (p2[0]-p1[0], p2[1]-p1[1])
                dir_vec, curr_len = normalize(curr_vec)
                
                if curr_len == 0: continue
                
                diff = curr_len - target_len
                # Move endpoints towards each other to match length
                # Move each by half the difference
                move_x = dir_vec[0] * diff * 0.5
                move_y = dir_vec[1] * diff * 0.5
                
                set_point(walls, (w_idx, 0), (p1[0] + move_x, p1[1] + move_y))
                set_point(walls, (w_idx, 1), (p2[0] - move_x, p2[1] - move_y))

            # --- EQUAL LENGTH ---
            elif ctype == 'EQUAL':
                # Targets: [w_idx1, w_idx2]
                w1 = walls[c['indices'][0]]
                w2 = walls[c['indices'][1]]
                
                l1 = length(w1['start'], w1['end'])
                l2 = length(w2['start'], w2['end'])
                
                avg_len = (l1 + l2) / 2.0
                
                # Apply to Wall 1
                p1s, p1e = list(w1['start']), list(w1['end'])
                v1, d1 = normalize((p1e[0]-p1s[0], p1e[1]-p1s[1]))
                diff1 = d1 - avg_len
                set_point(walls, (c['indices'][0], 0), (p1s[0] + v1[0]*diff1*0.5, p1s[1] + v1[1]*diff1*0.5))
                set_point(walls, (c['indices'][0], 1), (p1e[0] - v1[0]*diff1*0.5, p1e[1] - v1[1]*diff1*0.5))
                
                # Apply to Wall 2
                p2s, p2e = list(w2['start']), list(w2['end'])
                v2, d2 = normalize((p2e[0]-p2s[0], p2e[1]-p2s[1]))
                diff2 = d2 - avg_len
                set_point(walls, (c['indices'][1], 0), (p2s[0] + v2[0]*diff2*0.5, p2s[1] + v2[1]*diff2*0.5))
                set_point(walls, (c['indices'][1], 1), (p2e[0] - v2[0]*diff2*0.5, p2e[1] - v2[1]*diff2*0.5))

            # --- PARALLEL ---
            elif ctype == 'PARALLEL':
                # Targets: [w_idx1, w_idx2]
                # Rotate both to average angle
                w1 = walls[c['indices'][0]]
                w2 = walls[c['indices'][1]]
                
                dx1, dy1 = w1['end'][0] - w1['start'][0], w1['end'][1] - w1['start'][1]
                dx2, dy2 = w2['end'][0] - w2['start'][0], w2['end'][1] - w2['start'][1]
                
                a1 = math.atan2(dy1, dx1)
                a2 = math.atan2(dy2, dx2)
                
                # Check if anti-parallel (close to 180 deg diff) is closer
                if abs(a1 - a2) > math.pi/2:
                    # Make them point opposite ways but parallel lines
                    if a2 < a1: a2 += math.pi 
                    else: a2 -= math.pi
                
                avg_angle = (a1 + a2) / 2.0
                
                # Rotate w1
                c1 = list(w1['start']); c1_center = ((w1['start'][0]+w1['end'][0])/2, (w1['start'][1]+w1['end'][1])/2)
                l1 = length(w1['start'], w1['end']) / 2.0
                set_point(walls, (c['indices'][0], 0), (c1_center[0] - math.cos(avg_angle)*l1, c1_center[1] - math.sin(avg_angle)*l1))
                set_point(walls, (c['indices'][0], 1), (c1_center[0] + math.cos(avg_angle)*l1, c1_center[1] + math.sin(avg_angle)*l1))
                
                # Rotate w2
                c2_center = ((w2['start'][0]+w2['end'][0])/2, (w2['start'][1]+w2['end'][1])/2)
                l2 = length(w2['start'], w2['end']) / 2.0
                set_point(walls, (c['indices'][1], 0), (c2_center[0] - math.cos(avg_angle)*l2, c2_center[1] - math.sin(avg_angle)*l2))
                set_point(walls, (c['indices'][1], 1), (c2_center[0] + math.cos(avg_angle)*l2, c2_center[1] + math.sin(avg_angle)*l2))

            # --- PERPENDICULAR ---
            elif ctype == 'PERPENDICULAR':
                # Targets: [w_idx1, w_idx2]
                w1 = walls[c['indices'][0]]
                w2 = walls[c['indices'][1]]
                
                dx1, dy1 = w1['end'][0] - w1['start'][0], w1['end'][1] - w1['start'][1]
                dx2, dy2 = w2['end'][0] - w2['start'][0], w2['end'][1] - w2['start'][1]
                
                a1 = math.atan2(dy1, dx1)
                a2 = math.atan2(dy2, dx2)
                
                # Goal: a2 = a1 + 90 or a1 - 90
                # Current difference
                diff = a2 - a1
                # Target diff is pi/2 or -pi/2
                # Normalize diff to -pi to pi
                while diff > math.pi: diff -= 2*math.pi
                while diff < -math.pi: diff += 2*math.pi
                
                if diff > 0: target_diff = math.pi/2
                else: target_diff = -math.pi/2
                
                correction = (target_diff - diff) / 2.0
                
                t1 = a1 - correction
                t2 = a2 + correction
                
                # Rotate w1
                c1_center = ((w1['start'][0]+w1['end'][0])/2, (w1['start'][1]+w1['end'][1])/2)
                l1 = length(w1['start'], w1['end']) / 2.0
                set_point(walls, (c['indices'][0], 0), (c1_center[0] - math.cos(t1)*l1, c1_center[1] - math.sin(t1)*l1))
                set_point(walls, (c['indices'][0], 1), (c1_center[0] + math.cos(t1)*l1, c1_center[1] + math.sin(t1)*l1))
                
                # Rotate w2
                c2_center = ((w2['start'][0]+w2['end'][0])/2, (w2['start'][1]+w2['end'][1])/2)
                l2 = length(w2['start'], w2['end']) / 2.0
                set_point(walls, (c['indices'][1], 0), (c2_center[0] - math.cos(t2)*l2, c2_center[1] - math.sin(t2)*l2))
                set_point(walls, (c['indices'][1], 1), (c2_center[0] + math.cos(t2)*l2, c2_center[1] + math.sin(t2)*l2))