# https://programmers.co.kr/learn/courses/30/lessons/72413
# 2021 KAKAO BLIND RECRUITMENT 합승 택시 요금

import sys
from collections import deque


def solution(n, s, a, b, fares):
    path = [[0] * (n + 1) for _ in range(n + 1)]
    for f in fares:
        path[f[0]][f[1]], path[f[1]][f[0]] = f[2], f[2]

    shortest = [[sys.maxsize] * (n + 1) for _ in range(n + 1)]
    shortest[0][0] = 0
    for i in range(1, n + 1):
        shortest[i][i], shortest[0][i], shortest[i][0] = 0, 0, 0

    for idx in range(1, n + 1):
        q = deque()
        for i, x in enumerate(path[idx]):
            if x != 0:
                q.append(i)
                shortest[idx][i] = x

        visited = [0] * (n + 1)
        visited[0], visited[idx] = 1, 1
        while q:
            v = q.popleft()
            visited[v] = 1
            for i, x in enumerate(path[v]):
                if x == 0:
                    continue
                shortest[idx][i] = min(shortest[idx][v] + x, shortest[idx][i])
                if i != s and i not in q and visited[i] == 0:
                    q.append(i)

    answer = sys.maxsize
    for idx in range(1, n + 1):
        answer = min(answer, shortest[s][idx] + shortest[idx][a] + shortest[idx][b])

    return answer


if __name__ == '__main__':
    solution(6, 4, 6, 2, [[4, 1, 10], [3, 5, 24], [5, 6, 2], [3, 1, 41], [5, 1, 24], [4, 6, 50], [2, 4, 66], [2, 3, 22],
                          [1, 6, 25]])
    solution(7, 3, 4, 1, [[5, 7, 9], [4, 6, 4], [3, 6, 1], [3, 2, 3], [2, 1, 6]])
    solution(6, 4, 5, 6, [[2, 6, 6], [6, 3, 7], [4, 6, 7], [6, 5, 11], [2, 5, 12], [5, 3, 20], [2, 4, 8], [4, 3, 9]])
