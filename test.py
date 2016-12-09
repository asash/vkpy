import vk

while True:
    try:
        users = vk.get_group_subscribers(80270762)
        friends = vk.get_friends_map(users)
        for user in friends:
            pass
#            print(user)
    except KeyboardInterrupt :
        break

    except:
        continue
    
    break
        
info = vk.get_users_info(users)
for user in info:
    print(user)
