from main import assign_order, can_accept_order,select_vehicle,calculate_extra_minutes,build_extra_minutes

test_vehicles = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
                ]

test_result = assign_order(test_vehicles,1)
assert test_result == 10
assert test_vehicles[0]["passengers"] == 2

test_vehicles_2 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
                ]

test_result_2 = assign_order(test_vehicles_2,0)
assert test_result_2 is None
assert test_vehicles_2[0]["passengers"] == 1

test_vehicles_3 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
                ]
test_result_3 = assign_order(test_vehicles_3,-1)
assert test_result_3 is None
assert test_vehicles_3[0]["passengers"] == 1

test_vehicles_4 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
                ]
test_result_4 = assign_order(test_vehicles_4,2)
assert test_result_4 is None
assert test_vehicles_4[0]["passengers"] == 1

test_vehicles_5 = [
        {
        "id":10 ,
        "passengers":2 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":0 ,
        "capacity":2
        }
                ]
test_result_5 = assign_order(test_vehicles_5,1)
assert test_result_5 == 20
assert test_vehicles_5[0]["passengers"] == 2
assert test_vehicles_5[1]["passengers"] == 1

test_vehicles_6 = [
        {
        "id":10 ,
        "passengers":0 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":0 ,
        "capacity":2
        }
                ]
test_result_6 = assign_order(test_vehicles_6,1)
assert test_result_6 == 10
assert test_vehicles_6[0]["passengers"] == 1
assert test_vehicles_6[1]["passengers"] == 0



extra_minutes = {
    20: 3,
    10: 8,
    40: 3,
    30: 2
}
test_vehicles_7 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":2 ,
        "capacity":2
        },
        {
        "id":30 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":40 ,
        "passengers":1 ,
        "capacity":2
        },
                ]

test_result_7 = select_vehicle(test_vehicles_7,1,extra_minutes)
assert test_result_7 == 30


extra_minutes = {
    20: 3,
    10: 8,
    40: 3,
    30: 3
}
test_vehicles_8 = [
        {
        "id":30 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":2 ,
        "capacity":2
        },
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":40 ,
        "passengers":1 ,
        "capacity":2
        },
                ]

test_result_8 = select_vehicle(test_vehicles_8,1,extra_minutes)
assert test_result_8 == 30

extra_minutes = {
    10: 8,
    20: 3
}
test_vehicles_9 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_9 = assign_order(test_vehicles_9,1,extra_minutes)
assert test_result_9 == 20
assert test_vehicles_9[0]["passengers"] == 1
assert test_vehicles_9[1]["passengers"] == 2


extra_minutes = {
    20: 3
}
test_vehicles_10 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_10 = select_vehicle(test_vehicles_10,1,extra_minutes)
assert test_result_10 == 20
assert test_vehicles_10[0]["passengers"] == 1


extra_minutes = {
    10: 3,
    20: 3
}

pickup_minutes ={
    10 : 6,
    20 : 2
}
test_vehicles_10 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_10 = select_vehicle(test_vehicles_10,1,extra_minutes,pickup_minutes)
assert test_result_10 == 20
assert test_vehicles_10[0]["passengers"] == 1


extra_minutes = {
    10: 3,
    20: 3
}

pickup_minutes ={
    10 : 6,
    20 : 2
}
test_vehicles_11 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_11 = select_vehicle(test_vehicles_11,1,extra_minutes)
assert test_result_11 == 10



extra_minutes = {
    10: 3,
    20: 3
}

pickup_minutes ={
    10 : 6,
    20 : 2
}
test_vehicles_12 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_12 = assign_order(test_vehicles_12,1,extra_minutes,pickup_minutes)
assert test_result_12 == 20
assert test_vehicles_12[0]["passengers"] == 1
assert test_vehicles_12[1]["passengers"] == 2


extra_minutes = {
    10: 3,
    20: 3
}

pickup_minutes ={
    10 : 6,
    20 : 2
}
test_vehicles_12 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_12 = assign_order(test_vehicles_12,1,extra_minutes)
assert test_result_12 == 10
assert test_vehicles_12[0]["passengers"] == 2
assert test_vehicles_12[1]["passengers"] == 1


extra_minutes = {
    10: 3,
    20: 3
}

pickup_minutes ={
    20 : 2
}
test_vehicles_13 = [
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_13 = assign_order(test_vehicles_13,1,extra_minutes,pickup_minutes)
assert test_result_13 == 10


extra_minutes = {
    20: 5,
    10: 3
}

pickup_minutes ={
    20: 2,
    10: 6
}
test_vehicles_14 = [
        
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_14 = assign_order(test_vehicles_14,1,extra_minutes,pickup_minutes)
assert test_result_14 == 10


extra_minutes = {
    20: 11,
    10: 10
}

pickup_minutes ={
    20: 2,
    10: 6
}
test_vehicles_15 = [
        
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_15 = select_vehicle(test_vehicles_15,1,extra_minutes,pickup_minutes,max_extra_minutes=10)
assert test_result_15 == 10


extra_minutes = {
    20: 11,
    10: 11
}

pickup_minutes ={
    20: 2,
    10: 6
}
test_vehicles_16 = [
        
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

test_result_16 = assign_order(test_vehicles_16,1,extra_minutes,max_extra_minutes=10)
assert test_result_16 is None
assert test_vehicles_16[1]['passengers'] == 1

assert calculate_extra_minutes(18,23) == 5


test_vehicles_17 = [
        
        {
        "id":20 ,
        "passengers":1 ,
        "capacity":2
        },
        {
        "id":10 ,
        "passengers":1 ,
        "capacity":2
        }
       ]

original_minutes = {10: 18, 20: 15}
proposed_minutes = {10: 23, 20: 18}


extra_minutes = build_extra_minutes(original_minutes,proposed_minutes)

assert extra_minutes == {10: 5, 20: 3}

test_result17 = assign_order(test_vehicles_17,1,extra_minutes)
assert test_result17 == 20
assert test_vehicles_17[0]["passengers"] == 2
assert test_vehicles_17[1]["passengers"] == 1



order = {
    "passengers" : 1,
    "pickup_stop" : "A",
    "dropoff_stop" : "B"
}
