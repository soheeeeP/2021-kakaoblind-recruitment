from apscheduler.schedulers.background import BackgroundScheduler

from rest_framework import status
from rest_framework.response import Response

from kakaoblind2021 import settings

from model_utils import Choices

SERVER_STATUS = Choices(
    ('initial', 'initial'),
    ('in_progress', 'in_progress'),
    ('ready', 'ready'),
    ('finished', 'finished')
)

truck_command_dict = {
    0: '6초간 아무것도 하지 않음',
    1: '위로 한 칸 이동',
    2: '오른쪽으로 한 칸 이동',
    3: '아래로 한 칸 이동',
    4: '왼쪽으로 한 칸 이동',
    5: '자전거 상차',
    6: '자전거 하차'
}


class KakaoTScheduler(object):
    def __init__(self):
        self.scenario = 0                   # 시나리오 idx
        self.problem = None                 # 서버 시나리오
        self.runtime = 0                    # 서버 수행시간
        self.size = 0                       # 대여소 크기 (size*size)
        self.scheduler = BackgroundScheduler()
        self.server_status = SERVER_STATUS.initial  # 서버 상태 (initial, in_progress, ready, finished)

        self.rental = None                  # 자전거 대여 요청 처리 대기열
        self.back = {}                      # 자전거 반납 처리 대기열
        self.total_req_count = 0            # 자전거 대여 전체 요청 (트럭 이동 유무와 관계 없는 값, 하나의 시나리오에 대하여 고정된 값을 가짐)
        self.failed_req_count = 0           # 자전거 대여 실패 요청 (트럭 이동 유무에 따라 달라지는 값)

        self.commands = None                # 트럭 이동 명령어열
        self.total_truck_movement_dist = 0  # 트럭이 쉬지 않고 달린다고 가정할 때의 거리의 합
        self.actual_truck_movement_dist = 0 # 트럭 이동 거리

        self.score = 0.0

    def __del__(self):
        self.terminate_scheduler()

    def terminate_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def init_scheduler(self, scenario):
        self.scenario = scenario
        self.scheduler.start()
        self.server_status = SERVER_STATUS.in_progress
        self.scheduler.add_job(self.set_server_status_scheduler, "cron", second="*/1", id="server_status")

    def set_server_status_scheduler(self):
        # 서버가 수행한 simulate 요청이 720번 성공한 경우, 서버의 상태를 finished로 변경
        if self.total_req_count - self.failed_req_count >= 720:
            self.server_status = SERVER_STATUS.finished
            self.total_truck_movement_dist = self.total_req_count * self.size
            self.calc_server_score()

    def calc_server_score(self):
        # TODO: 트럭이 이동하는 경우, 이동하지 않는 경우의 req_count를 구분해야 한다
        S, _S = self.total_req_count, 0.0
        x = self.total_req_count - self.failed_req_count
        achievement_rate = (x - _S) / (S - _S) * 100
        T, t = self.total_truck_movement_dist, self.actual_truck_movement_dist
        efficiency_rate = (T - t) / T * 100
        self.score = max(achievement_rate * 0.95 + efficiency_rate * 0.05, self.score)

        self.problem.score.score = self.score
        self.problem.score.status = self.server_status
        self.problem.score.save()

    def add_bike_scheduler(self, problem, rental):
        self.problem = problem
        self.rental = rental
        self.size = getattr(settings, 'problem')[str(self.problem.idx)]['size']   # 대여소의 크기
        self.scheduler.add_job(self.bike_scheduler, "cron", second="*/1", id="bike")

    def add_truck_scheduler(self, commands):
        # 트럭이 행할 명령(현재 시각 ~ 현재 시각+1분)이 들어오는 경우, 함수로 요청 수행
        self.commands = commands
        self.truck_scheduler()

    def bike_scheduler(self):
        loc_set = self.problem.location_set.all()

        print("============ BIKE SCHEDULER ============")
        print('서버시간: ' + str(self.runtime))

        print('반납 처리 대기열: ', end='')
        print(self.back)

        # 현재 시간에 예정되어 있는 자전거 반납 처리
        if self.runtime in self.back:
            back_idx = self.back[self.runtime]
            for b in back_idx:
                loc = loc_set.get(idx=b)
                loc.bike += 1  # 반납할 대여소에 자전거 반납
                loc.save()
            # 반납 대기열에서 제거
            self.back.pop(self.runtime)

        if str(self.runtime) in self.rental:
            data = self.rental[str(self.runtime)]
            self.total_req_count += len(data)
            print('처리할 요청: ', end='')
            print(data)

            # 자전거 대여 요청 처리
            for d in data:
                # [자전거를 대여할 대여소 ID, 자전거를 반납할 대여소 ID, 이용시간(분)]
                loc = loc_set.get(idx=d[0])

                # 대여소에 자전거가 남아있지 않는 경우, 요청 실패 처리
                if loc.bike < 1:
                    self.failed_req_count += 1
                # 대여소에 자전거가 1대 이상 남아있는 경우, 자전거 대여
                else:
                    loc.bike -= 1
                    loc.save()
                    if self.server_status == SERVER_STATUS.in_progress:
                        self.server_status = SERVER_STATUS.ready

                    # 반납시간 계산
                    return_time = self.runtime + d[2]
                    print(f'ID {loc.idx}에서 자전거 대여. {return_time}분에 ID {d[1]}인 자전거 대여소에 반납 예정')
                    print(f'ID {loc.idx}에는 자전거 {loc.bike}대가 남음')
                    # 자전거 반납 대기열에 추가
                    if return_time not in self.back:
                        self.back[return_time] = [d[1]]
                    else:
                        self.back[return_time].append(d[1])
        print('취소된 요청 수: ' + str(self.failed_req_count))

        # 서버 실행 시간 업데이트
        self.runtime += 1

        print("사용자의 총 대여 요청 수: " + str(self.total_req_count))
        print("트럭이 아무것도 안했을 때 시나리오에서 성공하는 요청 수:" + str(self.total_req_count-self.failed_req_count))
        print("============ BIKE END ============")

    def truck_scheduler(self):
        truck_set = self.problem.truck_set.all()
        # ID가 낮은 트럭의 명령순으로 정렬
        c_queue = sorted(self.commands, key=lambda x: x['truck_id'])

        print("============ TRUCK SCHEDULER ============")
        print('서버시간: ' + str(self.runtime))

        for q in c_queue:
            t_idx, command = q['truck_id'], q['command']
            t = truck_set.get(idx=t_idx)
            # 'truck_id'를 ID로 가지는 트럭의 행(t_row), 열(t_row), 현재 위치(loc_idx)
            t_row, t_col, t_loc_idx = t.loc_row, t.loc_col, t.loc_idx
            print(f'truck은 현재 [{t_row}][{t_col}]: {t_loc_idx} 위치에 있으며 잔여 자젼거는 {t.bikes}대\n')
            for i, c in enumerate(command):
                # 트럭에게 내릴 수 있는 최대 명령 수(10개)를 초과하면, 그 이상은 실행하지 않음
                if i >= 10:
                    break
                # 트럭이 6초간 아무것도 하지 않는 경우
                if c == 0:
                    continue
                # 트럭이 상, 하, 좌, 우로 움직이는 경우
                elif c in [1, 2, 3, 4]:
                    t_loc_idx, t_row, t_col = self.truck_movement(size=self.size, t_loc_idx=t_loc_idx, t_row=t_row, t_col=t_col, command=c)
                    t.loc_idx = t_loc_idx
                    t.loc_row = t_row
                    t.loc_col = t_col
                # 트럭이 자전거 상, 하차 명령을 수행하는 경우
                else:
                    # bike = self.problem.location_set.get(idx=t_idx)
                    bike = self.problem.location_set.get(idx=t_loc_idx)
                    if c == 5 and bike.bike > 0:
                        t.bikes += 1
                        bike.bike -= 1
                        bike.save()
                    elif c == 6 and t.bikes > 0:
                        t.bikes -= 1
                        bike.bike += 1
                        bike.save()
                    # 자전거가 없는 대여소에서 상차를 하거나, 트럭에 자전거가 없는데 하차를 하려는 경우, 명령 무시
                    else:
                        continue
                t.save()
                print(f'{truck_command_dict[c]} -> loc_idx: {t_loc_idx}, row: {t_row}, col: {t_col}, bikes: {t.bikes}')

        # 처리한 트럭 이동 요청 대기열 비우기
        self.commands = None

        response = {
            "status": self.server_status,
            "time": self.runtime,
            "failed_request_count": self.failed_req_count,
            "distance": self.actual_truck_movement_dist
        }
        print(response)
        print("============ TRUCK END ============")
        return Response(response, status=status.HTTP_200_OK)

    def truck_movement(self, size=None, t_loc_idx=None, t_row=None, t_col=None, command=None):
        # 위로 한 칸 이동
        if command == 1 and 1 <= t_row - 1 <= size:
            self.actual_truck_movement_dist += 0.1
            return t_loc_idx + 1, t_row - 1, t_col
        # 오른쪽으로 한 칸 이동
        elif command == 2 and 1 <= t_col + 1 <= size:
            self.actual_truck_movement_dist += 0.1
            return t_loc_idx + size, t_row, t_col + 1
        # 아래로 한 칸 이동
        elif command == 3 and 1 <= t_row + 1 <= size:
            self.actual_truck_movement_dist += 0.1
            return t_loc_idx - 1, t_row + 1, t_col
        # 왼쪽으로 한 칸 이동
        elif command == 4 and 1 <= t_col - 1 <= size:
            self.actual_truck_movement_dist += 0.1
            return t_loc_idx - size, t_row, t_col - 1
        # 서비스 지역을 벗어나는 명령인 경우
        else:
            return t_loc_idx, t_row, t_col
