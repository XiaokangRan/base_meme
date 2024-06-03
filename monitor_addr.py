import time
from collections import defaultdict
import pandas as pd
import datetime
import os
import pickle
import sys
from web3 import Web3
from eth_abi import abi
import math
import random
import pymongo
from wechat import loop_send_wx_msg
import threading

os.environ['PROVIDER'] = "https://base.llamarpc.com"

provider = os.environ["PROVIDER"]
w3 = Web3(Web3.HTTPProvider(provider, request_kwargs={"timeout": 60}))
# Degen 合约地址：0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed
mongo_client = pymongo.MongoClient(host='localhost', port=27017)
db = mongo_client['monitor']
collection = db['monitor']
# 设置过期时间
collection.create_index([("time", pymongo.ASCENDING)], expireAfterSeconds=604800)

"""
1) 遍历记录所有的(receive_addr, token_addr)
2) 数据存入mongdb
3) 查询、过滤
"""


former_set = set()
fid_file = pd.read_csv("final_user_limit_1500_sorted.csv", index_col=None, header=None)
for index, row in fid_file.iterrows():
    former_addr = row[1]
    former_set.add(former_addr)


#eth usdc usdt
filter_token_set = set(["0x4200000000000000000000000000000000000006".lower(), "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed".lower(), "0x0000000000000000000000000000000000000000".lower()])

DECIMALS = math.pow(10, 18)
ONE_HOUR = 60 * 60

# 代币创建tx: 0xcea27f1618e28ecc59b2faed86cdec29a92218261fe9efe374a39201e93545c5
# base链每2秒一个区块, 一天43200个区块, 10天4ow, 100天400w个区块
START_BLOCK = 8925894

value = "Transfer(address,address,uint256)"
sha3_hash = Web3.keccak(text=value).hex()

myquery = {"name": "RUNOOB"}


# 查询过去一段时间的数据
"""
doc_filter = {
    "CompletionDateTime": {
        '$gte': start_of_day,  # 大于某个时间
        '$lt': end_of_day   # 小于某个时间
    }
}
"""
def search_mongo_at_hour(hours=1):
    doc_filter = {
        "time": {
            '$gte': datetime.datetime.utcnow() - datetime.timedelta(hours=hours)  # 大于多少时间的
        }
    }
    return collection.find(doc_filter)


# 统计token的次数
def process_data(collection_data):
    token_count_dict = defaultdict(int)
    addr_and_token_set = set()
    for item in collection_data:
        acc = item['acc']
        token = item['token']
        if acc + token not in addr_and_token_set:
            addr_and_token_set.add(acc + token)
            token_count_dict[token] += 1
    return token_count_dict


# 设置阈值并推送
def filter_and_push(time_delta, count_limit=5):
    push_message = []
    collection_data = search_mongo_at_hour(time_delta)
    token_count_dict = process_data(collection_data)
    for token_addr in token_count_dict.keys():
        token_count = token_count_dict[token_addr]
        if int(token_count) > count_limit:
            push_message.append(f"{token_addr} 人数: {token_count}  time_delta is {time_delta}")
    if push_message:
        # print("\n".join(push_message))
        loop_send_wx_msg("\n\n".join(push_message) + "\n")


# 定时任务
def schedule_task(time_delta):
    while True:
        filter_and_push(time_delta)
        time.sleep(time_delta * ONE_HOUR)


def process_log(latest_logs):
    res_list = []
    for log_item in latest_logs:

        # log的地址区分了大小写, 合于查询的地址都是小写
        call_addr = log_item['address'].lower()

        topic_data = log_item['topics']
        topic_0_sha3 = topic_data[0].hex()

        if call_addr not in filter_token_set and topic_0_sha3 == sha3_hash:
            transactionHash = log_item['transactionHash'].hex()
            # print(f"transactionHash is {transactionHash}")
            # blockNumber = log_item['blockNumber']

            data_data = log_item['data']  # .hex()

            transfer_from = abi.decode(['address'], topic_data[1])[0]
            transfer_to = abi.decode(['address'], topic_data[2])[0]

            transfer_from = str(transfer_from).lower()
            transfer_to = str(transfer_to).lower()

            if data_data.hex() == '0x' or transfer_to not in former_set:
                continue

            transfer_num = abi.decode(['uint256'], data_data)[0]/DECIMALS
            if int(transfer_num) > 0:
                res_list.append((transfer_to, call_addr, int(transfer_num), transfer_from))
                # print(f"transfer_from is {transfer_from}\ntransfer_to is {transfer_to}\ntransfer_num is {transfer_num}\n")
    return res_list


task1 = threading.Thread(target=schedule_task, args=(1,))
task2 = threading.Thread(target=schedule_task, args=(3,))
task3 = threading.Thread(target=schedule_task, args=(12,))
task4 = threading.Thread(target=schedule_task, args=(24,))
task5 = threading.Thread(target=schedule_task, args=(24 * 3,))

task1.start()
task2.start()
task3.start()
task4.start()
task5.start()

if __name__ == '__main__':

    start_block = w3.eth.block_number - 100

    i = 0
    while True:
        end_block = w3.eth.block_number
        t0 = time.time()

        mongo_list = []
        latest_logs = w3.eth.get_logs({'fromBlock': start_block, "toBlock": end_block,
                                       "topics": [
                                           "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]})

        transfer_list = process_log(latest_logs)
        # (transfer_to, call_addr, int(transfer_num), transfer_from)
        for item in transfer_list:
            receive_addr = item[0]
            token_addr = item[1]

            mongo_list.append({"acc": receive_addr, "token": token_addr, "time": datetime.datetime.utcnow()})

        if mongo_list:
            status = collection.insert_many(mongo_list)
            print(f"status is {status.inserted_ids}")

        t1 = time.time()
        run_delta = int(t1 - t0)

        if i % 1000 == 0:
            print(transfer_list)
            print(mongo_list)
        i += 1

        # break
        # 100个区块 需要200s
        time.sleep(200 - run_delta)
        start_block = end_block
