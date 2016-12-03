import urllib.parse
import requests
import sys
import json
import mmh3
from requests.exceptions import ReadTimeout
import networkx as nx
from pymongo import MongoClient
from tqdm import tqdm

mongo = MongoClient()
db = mongo.vk_cache
table = db.vk_cache

"""module implements some vk.com api methods wrappers"""

def vk_hash(string):
    return mmh3.hash64(string)[0]

def base_request(method, params, print_error=False, timeout=1):
    url = "http://api.vk.com/method/%s" % method
    doc = table.find_one({"_id": vk_hash(url + json.dumps(params))})
    if doc is not None:
        return doc['response']
    doc = {"_id": vk_hash(url + json.dumps(params))}
    while True:
        try:
            response = requests.post(url, data=dict(params), timeout=timeout)
            break
        except ReadTimeout:
            continue
    try:
        result = json.loads(response.text)
    except ValueError:
        return None
    if 'response' in result:
        doc['response'] = result['response']
        table.save(doc)
        return result['response']
    else:
        if print_error:
            sys.stderr.write(response.text)
        return None


def get_friends(user_id):
    res = base_request("friends.get", [('user_id', str(user_id))])
    if res is None:
        return []
    else:
        return res

def get_users_info(users_list, fields=None, show_pbar=None):
    result = {}
    batch_size = 500
    if fields is None:
        fields = ",".join(["sex", "bdate", "city", "country", "photo_50", "photo_100", "photo_200_orig",
                "photo_200", "photo_400_orig", "photo_max", "photo_max_orig", "photo_id", "online",
                "online_mobile", "domain", "has_mobile", "contacts", "connections", "site", "education",
                "universities", "schools", "can_post", "can_see_all_posts", "can_see_audio",
                "can_write_private_message", "status", "last_seen", "relation",
                "relatives", "counters", "screen_name", "maiden_name", "timezone", "occupation,activities",
                "interests", "music", "movies", "tv", "books", "games", "about", "quotes", "personal",
                "friends_status"])
    start = 0
    if show_pbar:
        pbar = tqdm(total=len(users_list))

    while start < len(users_list):
        if show_pbar:
            pbar.update(batch_size)
        request_ids = ",".join([str(id) for id in users_list[start:start+batch_size]])
        data = base_request("users.get", [("fields", fields), ("user_ids", request_ids)], True, timeout=5)
        for item in data:
            yield item
        start += batch_size


def get_n_users(users_cnt, fields=None, show_pbar=False, start_index=1):
    users_list = list(range(start_index, start_index+users_cnt))
    return get_users_info(users_list, fields, show_pbar)

def get_social_ball(user_id, ball_size):
    queue = [(user_id, 0)]
    graph = {}
    user_set = {user_id}
    while queue != [] and queue[0][1] <= ball_size:
        user, distance = queue[0]
        del(queue[0])
        user_friends = get_friends(user)
        graph[user] = user_friends
        for friend in user_friends:
            user_set.add(friend)
            queue.append((friend, distance+1))
    return graph, user_set

def nx_graph(vk_graph):
    friends_graph = nx.Graph()
    for uid in vk_graph.keys():
        for friend in vk_graph[uid]:
            friends_graph.add_edge(str(uid), str(friend))
    return friends_graph
