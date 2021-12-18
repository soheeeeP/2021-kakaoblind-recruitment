import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoT.models import Problem, SERVER_STATUS
from kakaoblind2021 import settings


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
    def __init__(self, problem, rental, truck_mode, commands):
        self.problem = problem
        self.runtime = 0
        self.scheduler = BackgroundScheduler()
        self.server_status = SERVER_STATUS.in_progress

        self.rental = rental                # 자전거 대여 요청 처리 대기열
        self.back = {}                      # 자전거 반납 처리 대기열
        self.total_bike_req_count = 0       # 자전거 대여 전체 요청
        self.failed_bike_req_count = 0      # 자전거 대여 실패 요청

        self.truck_mode = truck_mode        # 트럭 요청 수행 여부(True/False)
        self.commands = commands            # 트럭 이동 명령어열
        self.truck_movement_dist = 0        # 트럭 이동 거리
        self.total_truck_req_count = 0      # 트럭 이동 전체 요청
        self.failed_truck_req_count = 0     # 트럭 이동 실패 요청

    def __del__(self):
        self.terminate_scheduler()

    def terminate_scheduler(self):
        self.scheduler.shutdown()

    def init_scheduler(self):
        print(self.rental)
        self.scheduler.start()
        self.scheduler.add_job(self.set_server_status_scheduler, "cron", second="*/1", id="server_status")
        self.scheduler.add_job(self.bike_scheduler, "cron", second="*/1", id="bike")
        if self.truck_mode:
            self.scheduler.add_job(self.truck_scheduler, "cron", second="*/1", id="truck")

    def set_server_status_scheduler(self):
        bike_success = (self.total_bike_req_count - self.failed_bike_req_count)
        truck_success = (self.total_truck_req_count - self.failed_truck_req_count)
        # 서버가 수행한 simulate 요청이 720번 성공한 경우, 서버의 상태를 finished로 변경, 점수 계산
        if bike_success + truck_success >= 720:
            self.server_status = SERVER_STATUS.finished

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
            self.total_bike_req_count += len(data)
            print('처리할 요청: ', end='')
            print(data)

            # 자전거 대여 요청 처리
            for d in data:
                # [자전거를 대여할 대여소 ID, 자전거를 반납할 대여소 ID, 이용시간(분)]
                loc = loc_set.get(idx=d[0])

                # 대여소에 자전거가 남아있지 않는 경우, 요청 실패 처리
                if loc.bike < 1:
                    self.failed_bike_req_count += 1
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
        print('취소된 요청 수: ' + str(self.failed_bike_req_count))

        # 서버 실행 시간 업데이트
        self.runtime += 1

        print("사용자의 총 대여 요청 수: " + str(self.total_bike_req_count))
        print("트럭이 아무것도 안했을 때 시나리오에서 성공하는 요청 수:" + str(self.total_bike_req_count-self.failed_bike_req_count))

    def truck_scheduler(self):
        size = getattr(settings, 'problem')[self.problem.idx]   # 대여소의 크기
        truck_set = self.problem.truck_set.all()
        # ID가 낮은 트럭의 명령순으로 정렬
        c_queue = self.commands.sort(key=lambda x: x[0])

        print("============ TRUCK SCHEDULER ============")
        print('서버시간: ' + str(self.runtime))

        for q in c_queue:
            print("요청1 : " + str(q))
            t_idx, command = q['truck_id'], q['command']
            t = truck_set.get(idx=t_idx)
            # 'truck_id'를 ID로 가지는 트럭의 행(t_row), 열(t_row), 현재 위치(loc_idx)
            t_row, t_col, t_loc_idx = t.loc_row, t.loc_col, t.loc_idx
            print(f'truck은 현재 [{t_row}][{t_col}]: {t_loc_idx} 위치에 있으며 잔여 자젼거는 {t.bikes}대')
            for i, c in enumerate(command):
                # 트럭에게 내릴 수 있는 최대 명령 수(10개)를 초과하면, 그 이상은 실행하지 않음
                if i >= 10:
                    break
                print(f'{truck_command_dict[c]}', end=' ')
                self.total_truck_req_count += 1
                # 트럭이 6초간 아무것도 하지 않는 경우
                if c == 0:
                    continue
                # 트럭이 상, 하, 좌, 우로 움직이는 경우
                elif c in [1, 2, 3, 4]:
                    t_loc_idx, t_row, t_col = self.truck_movement(size=size, t_loc_idx=t_loc_idx, t_row=t_row, t_col=t_col, command=c)
                    t.loc_idx = t_loc_idx
                    t.loc_row = t_row
                    t.loc_col = t_col
                # 트럭이 자전거 상, 하차 명령을 수행하는 경우
                else:
                    bike = self.problem.location_set.get(idx=t_idx)
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
                        self.failed_truck_req_count += 1
                t.save()
                print(f'  -> loc_idx: {t_loc_idx}, row: {t_row}, col: {t_col}, bikes: {t.bikes}')

        response = {
            "status": self.server_status,
            "time": self.runtime,
            "failed_request_count": self.failed_bike_req_count + self.failed_truck_req_count,
            "distance": self.truck_movement_dist / 1000
        }
        return Response(response, status=status.HTTP_200_OK)

    def truck_movement(self, size=None, t_loc_idx=None, t_row=None, t_col=None, command=None):
        # 위로 한 칸 이동
        if command == 1 and 1 <= t_row - 1 <= size:
            self.truck_movement_dist += 100
            return t_loc_idx + 1, t_row - 1, t_col
        # 오른쪽으로 한 칸 이동
        elif command == 2 and 1 <= t_col + 1 <= size:
            self.truck_movement_dist += 100
            return t_loc_idx + size, t_row, t_col + 1
        # 아래로 한 칸 이동
        elif command == 3 and 1 <= t_row + 1 <= size:
            self.truck_movement_dist += 100
            return t_loc_idx - 1, t_row + 1, t_col
        # 왼쪽으로 한 칸 이동
        elif command == 4 and 1 <= t_col - 1 <= size:
            self.truck_movement_dist += 100
            return t_loc_idx - size, t_row, t_col - 1
        # 서비스 지역을 벗어나는 명령인 경우
        else:
            self.failed_truck_req_count += 1
            return t_loc_idx, t_row, t_col


class SimulateView(generics.CreateAPIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://grepp-cloudfront.s3.ap-northeast-2.amazonaws.com/programmers_imgs/competition-imgs/2021kakao/problem"

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        auth_key = request.META.get('HTTP_AUTHORIZATION')
        try:
            p = Problem.objects.prefetch_related('location_set', 'truck_set').get(auth_key=auth_key)
            idx = p.idx
        except Problem.DoesNotExist:
            message = "INVALID AUTH_KEY ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        req_url = self.base_url + str(idx) + "_day-1.json"
        rental_req_data = requests.get(req_url).json()

        commands = json.loads(request.POST['commands'])
        if commands:    # 트럭 이동 요청이 들어온 경우
            kakao = KakaoTScheduler(problem=p, rental=rental_req_data, truck_mode=True, commands=commands)
        else:           # 트럭 이동 없이 자전거 대여 요청만 수행하는 경우
            kakao = KakaoTScheduler(problem=p, rental=rental_req_data, truck_mode=False, commands=None)
        transaction.on_commit(lambda: kakao.init_scheduler())

        response = {
            "status": kakao.server_status,
            "time": kakao.runtime,
            "failed_requests_count": kakao.failed_bike_req_count + kakao.failed_truck_req_count,
            "distance": kakao.truck_movement_dist / 1000
        }
        return Response(response, status=status.HTTP_200_OK)
