# 2021 카카오 신입 공채 2차 온라인 코딩 테스트

#### 카카오 T 바이크 관리 시뮬레이션
> 카카오 T 바이크는 카카오 모빌리티에서 제공하는 전기 자전거 대여 서비스이다.
> 서비스의 문제점은 어떤 지역은 대여 수요는 많으나 반납되는 자전거가 없어 자전거가 부족하고,
> 반대로 어떤 지역은 반납되는 자전거는 많지만 대여 수요가 없어 자전거가 쌓이기만 한다는 것이다.
> 이런 현상을 해결하기 위해 신입사원 죠르디에게는 트럭으로 자전거를 재배치하라는 업무가 주어졌다.
> 지원자는 죠르디를 도와 자전거가 많이 대여될 수 있도록 트럭을 운영해보자.

#### 목표
> 트럭을 효율적으로 운영하여 대여소에 취소되는 대여 요청 수를 최대한 줄인다. 단, 트럭은 최대한 적게 움직이는 것이 좋다.

&nbsp;

## 언어 및 프레임워크
|<img src="https://user-images.githubusercontent.com/55832904/146668666-cd8127f5-23ed-43f8-8f77-553c62b43681.png" width="80" height="10%"><br>Python|<img src="https://user-images.githubusercontent.com/55832904/146668659-6d9a7e48-39c2-4a3c-bfc4-740c614bf476.png" width="80" height="10%"><br>Django|
|:--:|:--:|

&nbsp;

## 프로젝트 설계 및 구조

### 프로젝트 설계
* 서버 데이터를 관리할 Django `Model` 생성
* 자전거 대여 요청 및 트럭 명령을 수행하는 `custom scheduler` class 구현
  * `settings.py`에서 객체를 할당하여 프로젝트 변수로 사용
  * 서버 상태는 scheduler의 인스턴스 변수로 관리

|![instance method](https://user-images.githubusercontent.com/55832904/146671563-832007f0-d2ae-4d90-875d-a6c3fd02fd53.png) |![instance variable](https://user-images.githubusercontent.com/55832904/146671568-24c2a9a3-0981-4298-812d-90c6d8912806.png)|
|:--:|:--:|

``` Python
# settings.py

from utils.scheduler import KakaoTScheduler
kakao = KakaoTScheduler()
```
  
* 시나리오의 data를 별도의 `json` 파일로 관리
  * `settings.py`에서 동적으로 import하여 프로젝트 변수로 사용
``` Python
# settings.py

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_BASE_FILE = os.path.join(BASE_DIR, 'scenario.json')

scenario = json.loads(open(SECRET_BASE_FILE).read())
for key, value in scenario.items():
    setattr(sys.modules[__name__], key, value)
```
``` json
{
  "X_AUTH_TOKEN": "170cd6377c41574b2b115e95e6f7de23",
  "problem": {
    "1" : {
      "size" : 5,
      "bike" : 100,
      "truck" : 5,
      "total_req" : 1428,
      "success_req_no_truck" : 1077,
      "truck_dist" : 3600
    },
    "2" : {
      "size" : 60,
      "bike" : 10800,
      "truck" : 10,
      "total_req" : 10829,
      "success_req_no_truck" : 9142,
      "truck_dist" : 7200
    }
  }
}
```

### Model Dependency Diagram
<p align="center">
  <img src="https://user-images.githubusercontent.com/55832904/146669924-5a8e32e1-6d68-44fe-b0bb-c26942cf7f64.png" alt="Model Dependency Diagram"/>
</p>

#### Problem
> 시나리오(1<=idx<=2) 정보
>|Name|Type|Description| 
>|------|---|---|
>|idx|Integer|시나리오 번호 (1 <= problem <= 2)|
>|auth_key|UUID|Start API를 통해 발급받는 시나리오 key|
#### Location
> 대여소 정보 (서비스 지역의 크기: N*N)
>|Name|Type|Description| 
>|------|---|---|
>|problem|ForeignKey|시나리오 정보|
>|bike|Integer|대여소에 남아있는 자전거 수|
>|row|Integer|대여소의 격자 row(1<=row<=N)|
>|col|Integer|대여소의 격자 col(1<=col<=N)|
>|idx|Integer|대여소의 ID(0<=ID<=N*N-1)|
#### Truck
> 트럭 정보
>|Name|Type|Description| 
>|------|---|---|
>|problem|ForeignKey|시나리오 정보|
>|idx|Integer|트럭의 ID|
>|bikes|Integer|트럭에 실려있는 자전거 수|
>|loc_row|Integer|트럭이 위치하고 있는 격자 row(1<=row<=N)|
>|loc_col|Integer|트럭이 위치하고 있는 격자 col(1<=col<=N)|
>|loc_idx|Integer|트럭이 위치하고 있는 대여소 ID(0<=ID<=N*N-1)|
#### Score
> 점수 정보
>|Name|Type|Description| 
>|------|---|---|
>|problem|ForeignKey|시나리오 정보|
>|score|Integer|시나리오의 점수|
>|status|String|시나리오를 수행 중인 서버의 상태(`initial`, `in_progress`, `ready`, `finisihed`)|
 
### 프로젝트 구조
```
.
├── README.md
├── db.sqlite3
├── kakaoT
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── kakaoblind2021
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── scenario.json
├── server
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── templates
└── utils
    └── scheduler.py (요청을 수행하는 BackGroundScheduler)
```
    
### API endpoint
* `issue를` 통한 task로 관리 & 구현
<img src="https://user-images.githubusercontent.com/55832904/146669417-4a4610eb-9543-4cf6-adb2-6d49ecb9269d.png" width="70%">

#### [Start API](https://github.com/soheeeeP/2021-kakaoblind-recruitment/issues/2)
> 문제를 풀기 위한 key를 발급한다.
> **Start API**를 생성하면 파라미터로 전달한 문제 번호에 맞게 각 자전거 대여소 및 트럭에 대한 정보를 초기화한다.

#### [Locations API](https://github.com/soheeeeP/2021-kakaoblind-recruitment/issues/3)
> 현재 카카오 T 바이크 서비스 시각에 각 자전거 대여소가 보유한 자전거 수를 반환한다.

#### [Trucks API](https://github.com/soheeeeP/2021-kakaoblind-recruitment/issues/4)
> 현재 카카오 T 바이크 서비스 시각에 각 트럭의 위치와 싣고 있는 자전거 수를 반환한다.

#### [Simulate API](https://github.com/soheeeeP/2021-kakaoblind-recruitment/issues/5)
> 현재 시각 ~ 현재 시각 + 1분 까지 각 트럭이 행할 명령을 담아 서버에 전달한다.

#### [Score API](https://github.com/soheeeeP/2021-kakaoblind-recruitment/issues/6)
> 해당 `Auth key`로 획득한 점수를 반환한다. 점수는 높을수록 좋다. 
> 카카오 T 바이크 서버의 상태가 `finished`가 아닐 때 본 API를 호출하면 response의 score는 무조건 0.0이다.

&nbsp;

## 결과

&nbsp;

## 개선점
