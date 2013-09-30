import logging

from celery import task
from django.template.defaultfilters import slugify

import games.models
from accounts.models import User

LOGGER = logging.getLogger()


def create_game(game):
    steam_game = games.models.Game(
        name=game['name'],
        steamid=game['appid'],
    )
    if game['img_logo_url']:
        steam_game.get_steam_logo(game['img_logo_url'])
    steam_game.get_steam_icon(game['img_icon_url'])
    steam_game.save()
    return steam_game


@task
def sync_steam_library(user_id):
    user = User.objects.get(pk=user_id)
    steamid = user.get_profile().steamid
    steam_games = games.util.steam.steam_sync(steamid)
    for game in steam_games:
        print game['name']
        try:
            steam_game = games.models.Game.objects.get(steamid=game['appid'])
        except games.models.Game.DoesNotExist:
            if not game['img_icon_url']:
                continue

            existing_game = games.models.Game.objects.filter(
                slug=slugify(game['name'])
            )
            if not existing_game:
                steam_game = create_game(game)
            else:
                existing_game[0].appid = game['appid']
                existing_game[0].save()
        library = games.models.GameLibrary.objects.get(user=user)
        library.games.add(steam_game)