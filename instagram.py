from instagrapi import Client
from instaloader import Instaloader, Profile
import time
import random

def login_instagram(username, password):
    cl = Client()
    cl.login(username, password)
    return cl

def get_engaged_users(insta_username, max_posts=3):
    L = Instaloader()
    profile = Profile.from_username(L.context, insta_username)
    engaged_users = set()

    for post in profile.get_posts()[:max_posts]:
        for like in post.get_likes():
            engaged_users.add(like.username)
    return list(engaged_users)

def like_and_follow(cl, usernames, user_id=None, stop_flags=None, report=[]):
    for username in usernames:
        if stop_flags and stop_flags.get(user_id) == "stop":
            print("Остановлено пользователем.")
            break
        try:
            ig_user_id = cl.user_id_from_username(username)
            cl.user_follow(ig_user_id)
            medias = cl.user_medias(ig_user_id, 2)
            for media in medias:
                cl.media_like(media.id)
            report.append(username)
            print(f"Подписались и лайкнули: {username}")
            time.sleep(random.randint(30, 60))
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(random.randint(20, 40))