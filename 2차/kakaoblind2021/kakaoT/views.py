import uuid

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoblind2021 import settings
from kakaoT.models import Problem, Location, Truck, Score
from utils.scheduler import SERVER_STATUS


class StartView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        req_token = request.META.get('HTTP_X_AUTH_TOKEN')
        if req_token != getattr(settings, 'X_AUTH_TOKEN'):
            message = "INVALID X_AUTH_TOKEN ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        idx = request.query_params.get('problem')
        scenario = getattr(settings, 'problem')[idx]

        # 대여소 생성 (row, col, id, 자전거 대수)
        size = scenario['size']
        bike = scenario['bike'] / (size ** 2)

        try:
            # 다시 같은 시나리오를 simulate하는 경우
            p = Problem.objects.prefetch_related('location_set', 'truck_set', 'score').get(idx=idx)
            # 새로운 auth_key 발급
            p.auth_key = uuid.uuid4()

            # Problem을 참조하고 있는 Place와 Truck object 삭제
            # p.location_set.all().delete()
            # p.truck_set.all().delete()

            # Problem을 참조하고 있는 Place와 Truck object의 데이터 초기화
            loc_set = p.location_set.all()
            for l in loc_set.iterator():
                l.bike = bike
                l.save()

            truck_set = p.truck_set.all()
            for t in truck_set.iterator():
                t.loc_row, t.loc_col, t.loc_idx, t.bikes = size, 1, 0, 0
                t.save()

            score = p.score
            score.score, score.status = 0.0, SERVER_STATUS.initial
            score.save()

            p.save()

        except Problem.DoesNotExist:
            # 새로운 시나리오를 simulate하는 경우
            with transaction.atomic():
                # Problem 시나리오 생성
                p = Problem.objects.create(
                    idx=idx,
                    auth_key=uuid.uuid4()
                )

                idx = 0
                for i in range(1, size + 1, 1):
                    for j in range(size, 0, -1):
                        Location.objects.create(
                            problem_id=p.id,
                            idx=idx,
                            row=i,
                            col=j,
                            bike=bike
                        )
                        idx += 1

                # 트럭 생성 (시작 위치 [0,0])
                truck = scenario['truck']
                idx = 0
                for i in range(truck):
                    Truck.objects.create(
                        problem_id=p.id,
                        idx=idx,
                        loc_row=size
                    )
                    idx += 1
                Score.objects.create(problem=p)
        finally:
            response = {
                "auth_key": p.auth_key,
                "problem": p.idx,
                "time": 0
            }
            return Response(response, status=status.HTTP_201_CREATED)


class LocationView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        auth_key = request.META.get('HTTP_AUTHORIZATION')
        try:
            p = Problem.objects.prefetch_related('location_set').get(auth_key=auth_key)
        except Problem.DoesNotExist:
            message = "INVALID AUTH_KEY ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        data = []
        locations = p.location_set.all()
        for loc in locations.iterator():
            data.append({
                "id": loc.idx,
                "located_bikes_count": loc.bike
            })
        return Response({"locations": data}, status=status.HTTP_200_OK)


class TruckView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        auth_key = request.META.get('HTTP_AUTHORIZATION')
        try:
            p = Problem.objects.prefetch_related('truck_set').get(auth_key=auth_key)
        except Problem.DoesNotExist:
            message = "INVALID AUTH_KEY ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        data = []
        trucks = p.truck_set.all()
        for truck in trucks.iterator():
            data.append({
                "id": truck.idx,
                "location_id": truck.loc_idx,
                "located_bikes_cnt": truck.bikes
            })
        return Response({"trucks": data}, status=status.HTTP_200_OK)


class ScoreView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        auth_key = request.META.get('HTTP_AUTHORIZATION')
        try:
            s = Score.objects.get(problem__auth_key=auth_key)
        except Score.DoesNotExist:
            message = "INVALID AUTH_KEY ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        if s.status != SERVER_STATUS.finished:
            score = 0.0
        else:
            score = s.score

        response = {"score": score}
        return Response(response, status=status.HTTP_200_OK)
