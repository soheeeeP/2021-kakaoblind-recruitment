import json
import requests

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoT.models import Problem, SERVER_STATUS
from utils.scheduler import KakaoTScheduler


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
