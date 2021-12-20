# https://programmers.co.kr/learn/courses/30/lessons/72412
# 2021 KAKAO BLIND RECRUITMENT 순위 검색

def solution(info, query):
    language = {'java': set(), 'python': set(), 'cpp': set()}
    part = {'backend': set(), 'frontend': set()}
    career = {'junior': set(), 'senior': set()}
    food = {'pizza': set(), 'chicken': set()}
    score = []

    for i, line in enumerate(info):
        x = line.split()
        language[x[0]].add(i)
        part[x[1]].add(i)
        career[x[2]].add(i)
        food[x[3]].add(i)
        score.append(int(x[4]))

    result = []
    temp = {idx for idx in range(len(info))}
    for i, q in enumerate(query):
        x = q.split()
        cnt = temp
        if x[0] != "-":
            cnt = cnt.intersection(language[x[0]])
        if x[2] != "-":
            cnt = cnt.intersection(part[x[2]])
        if x[4] != "-":
            cnt = cnt.intersection(career[x[4]])
        if x[6] != "-":
            cnt = cnt.intersection(food[x[6]])
        answer = 0
        for c in cnt:
            if int(score[c]) >= int(x[7]):
                answer += 1
        result.append(answer)
    print(result)
    return result


if __name__ == '__main__':
    solution(
        ["java backend junior pizza 150", "python frontend senior chicken 210", "python frontend senior chicken 150",
         "cpp backend senior pizza 260", "java backend junior chicken 80", "python backend senior chicken 50"],
        ["java and backend and junior and pizza 100", "python and frontend and senior and chicken 200",
         "cpp and - and senior and pizza 250", "- and backend and senior and - 150", "- and - and - and chicken 100",
         "- and - and - and - 150"])
