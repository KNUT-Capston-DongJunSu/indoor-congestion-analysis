def calc_spatial_density(tracked_objects, scale=1000):
    centers = []
    for x1, y1, x2, y2, *_ in tracked_objects:
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        centers.append((cx, cy))

    # 한 개 이하일 경우 거리 개념 없음
    if len(centers) < 2:
        return 0.0

    total_dist = 0
    count = 0
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            dx = centers[i][0] - centers[j][0]
            dy = centers[i][1] - centers[j][1]
            total_dist += (dx * dx + dy * dy) ** 0.5
            count += 1      
    avg_dist = total_dist / count
    return len(centers) / (avg_dist + 1e-6) * scale # 0 나누기 방지
