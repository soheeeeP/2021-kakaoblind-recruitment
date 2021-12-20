# https://programmers.co.kr/learn/courses/30/lessons/72413
# 2021 KAKAO BLIND RECRUITMENT 합승 택시 요금

def solution(n, s, a, b, fares):
    path = [[10000001] * (n + 1) for _ in range(n + 1)]
    path[0][0] = 0
    for i in range(1, n + 1):
        path[i][i], path[0][i], path[i][0] = 0, 0, 0
    for f in fares:
        path[f[0]][f[1]], path[f[1]][f[0]] = f[2], f[2]

    # 플로이드-와샬(Floyd-Warshall) 적용하여 단순화
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                path[i][j] = min(path[i][j], path[i][k] + path[k][j])

    answer = 10000001
    for idx in range(1, n + 1):
        answer = min(answer, path[s][idx] + path[idx][a] + path[idx][b])

    return answer


if __name__ == '__main__':
    solution(6, 4, 6, 2, [[4, 1, 10], [3, 5, 24], [5, 6, 2], [3, 1, 41], [5, 1, 24], [4, 6, 50], [2, 4, 66], [2, 3, 22],
                          [1, 6, 25]])
    solution(7, 3, 4, 1, [[5, 7, 9], [4, 6, 4], [3, 6, 1], [3, 2, 3], [2, 1, 6]])
    solution(6, 4, 5, 6, [[2, 6, 6], [6, 3, 7], [4, 6, 7], [6, 5, 11], [2, 5, 12], [5, 3, 20], [2, 4, 8], [4, 3, 9]])
