import vk

users = vk.get_group_subscribers(80270762)
friends = vk.get_friends_multiprocess(users)
for user in friends:
    print(user)
