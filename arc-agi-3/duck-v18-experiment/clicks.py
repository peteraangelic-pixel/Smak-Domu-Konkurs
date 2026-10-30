def wm_click_actions(frame, transitions, limit=16):
    """Bounded click vocabulary from the visible grid and observed changes."""
    from collections import Counter, deque
    grid = getattr(frame, "_grid", None)
    if grid is None or len(grid) == 0 or len(grid[0]) == 0:
        return []
    height, width = len(grid), len(grid[0])
    points = {}
    for event in reversed(list(transitions or [])[-64:]):
        before, after = event.before_frame, event.after_frame
        if before.level != frame.level or after.level != frame.level:
            continue
        act = wm_parse_action(event.action)
        if isinstance(act, dict) and act.get("action") == "MOUSE" and before.ascii != after.ascii:
            r, c = act.get("row"), act.get("col")
            if isinstance(r, int) and isinstance(c, int) and 0 <= r < height and 0 <= c < width:
                points[r, c] = None
                if len(points) >= limit // 2:
                    break
    counts = Counter(v for row in grid for v in row)
    background = counts.most_common(1)[0][0]
    seen = set()
    groups = {}
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == background or (r, c) in seen:
                continue
            component = [(r, c)]
            seen.add((r, c))
            for y, x in component:
                for pos in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    a,b = pos
                    if 0 <= a < height and 0 <= b < width and pos not in seen and grid[a][b] == color:
                        component.append(pos)
                        seen.add(pos)
            cy = sum(y for y,x in component) / len(component)
            cx = sum(x for y,x in component) / len(component)
            center = min(component, key=lambda p: (p[0]-cy)**2 + (p[1]-cx)**2)
            groups.setdefault(color, []).append((-len(component), center))
    queues = [deque(sorted(groups[k])) for k in sorted(groups, key=counts.get)]
    while queues and len(points) < limit:
        for queue in queues:
            points[queue.popleft()[1]] = None
            if len(points) == limit:
                break
        queues = [q for q in queues if q]
    return [{"action":"MOUSE","row":y,"col":x} for y,x in points]
