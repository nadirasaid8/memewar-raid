import os
import asyncio
import random
import json
import re
import aiohttp
import random
from colorama import *
from datetime import datetime
from urllib.parse import quote, unquote, parse_qs
from src.deeplchain import kng, pth, hju, mrh, bru, htm, countdown_timer, log, _banner, _clear, read_config, log_error

init(autoreset=True)

class MemesWarBot:
    def __init__(self):
        self.config = read_config()
        self.base_url = "https://memes-war.memecore.com/api"
        self.query_id_user_agent_map = {}
        self.proxies = self.load_proxies()

        with open('src/lock-agent.txt', 'r') as file:
            self.user_agents = file.read().strip().split('\n')

        with open('data.txt', 'r') as file:
            self.query_ids = file.read().strip().split('\n')

        self.leaders = ['elon', 'ant', 'bonk', 'cz', 'doge', 'floki', 'kamala', 'pepe', 'shib', 'wif']
        self.members = ['archer', 'ninja', 'police', 'solder']

    def load_proxies(self):
        proxies_file = os.path.join(os.path.dirname(__file__), './proxies.txt')
        formatted_proxies = []
        with open(proxies_file, 'r') as file:
            for line in file:
                proxy = line.strip()
                if proxy:
                    if proxy.startswith("socks5://"):
                        formatted_proxies.append(proxy)
                    elif not (proxy.startswith("http://") or proxy.startswith("https://")):
                        formatted_proxies.append(f"http://{proxy}")
                    else:
                        formatted_proxies.append(proxy)
        return formatted_proxies
    
    def is_valid_user_agent(self, user_agent):
        if not user_agent or not isinstance(user_agent, str):
            return False
        forbidden_chars_regex = r'[\n\r\t\b\f\v]'
        return not bool(re.search(forbidden_chars_regex, user_agent))

    def get_random_user_agent(self):
        random_user_agent = None
        while not random_user_agent or not self.is_valid_user_agent(random_user_agent):
            random_user_agent = random.choice(self.user_agents).strip()
        return random_user_agent

    async def get_user_info(self, query_id, proxy, session):
        try:
            encoded_query_id = quote(query_id)
            headers = {
                'Cookie': f'telegramInitData={encoded_query_id}',
                'User-Agent': self.query_id_user_agent_map.get(query_id)
            }
            
            async with session.get(f'{self.base_url}/user', headers=headers, proxy=proxy) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as error:
            log(mrh + f'Error getting user info: detail on last.log!')
            log_error(f"{error}")

    async def fetch_guilds(self, query_id, proxy, session):
        encoded_query_id = quote(query_id)
        headers = {
            'Cookie': f'telegramInitData={encoded_query_id}',
            'User-Agent': self.query_id_user_agent_map.get(query_id)
        }
        try:
            async with session.get(f'{self.base_url}/raid', headers=headers, proxy=proxy) as response:
                response.raise_for_status()
                data = await response.json()
                guilds = data.get("data", [])

                sorted_guilds = sorted(guilds, key=lambda g: g['warbondRank'], reverse=True)
                return sorted_guilds

        except aiohttp.ClientResponseError as e:
            log_error(f"Error fetching guilds: {e}")
            return []

    async def perform_raid(self, query_id, proxy, session, target_guild_id):
        encoded_query_id = quote(query_id)
        headers = {
            'Cookie': f'telegramInitData={encoded_query_id}',
            'User-Agent': self.query_id_user_agent_map.get(query_id),
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        leader = random.choice(self.leaders)
        member = random.choice(self.members)

        payload = {
            'leader': leader,
            'member': member,
            'target': target_guild_id
        }

        try:
            async with session.post(f'{self.base_url}/raid', data=payload, headers=headers, proxy=proxy) as response:
                response.raise_for_status()
                result = await response.json()
                is_win = result.get("data", {}).get("isWin", False)

                if is_win:
                    log(hju + f"Raid WIN: {pth}{leader} {hju}and {pth}{member} {hju}attacked guild {pth}{target_guild_id}")
                    log(hju + f"Result: Got Warbond: {pth}{result['data']['moveWarbond']} {hju}| Warbond Portion: {pth}{result['data']['warbondPortion']}")
                else:
                    log(mrh + f"Raid LOSE: {pth}{leader} {mrh}and {pth}{member} {mrh}attacked guild {pth}{target_guild_id}")
                    log(mrh + f"Result: Lost Warbond: {pth}{result['data']['moveWarbond']} {mrh}| Warbond Portion: {pth}{result['data']['warbondPortion']}")

        except aiohttp.ClientResponseError as e:
            log(bru + f"Skipping this raid due to error: details on last.log")
            log_error(f"{e}")
        except Exception as e:
            log_error(mrh + f"Unexpected error: {e}")

    async def main(self):
        use_proxy = self.config.get('use_proxy', False)
        min_raid_delay = self.config.get('min_raid_delay', 6)
        max_raid_delay = self.config.get('max_raid_delay', 12)
        raid_count = self.config.get('raid_count', 5) 
        countdown_loop = self.config.get('countdown_loop', 3800)
        total = len(self.query_ids)
        proxy_index = 0

        async with aiohttp.ClientSession() as session:
            while True:
                for idx, query_id in enumerate(self.query_ids):
                    decoded_data = unquote(query_id)
                    parsed_data = parse_qs(decoded_data)
                    user_json = parsed_data.get('user', [None])[0]

                    user_info = None
                    proxy = None
                    if user_json:
                        try:
                            user_info = json.loads(user_json)
                        except json.JSONDecodeError as error:
                            log(f'Error parsing user JSON: {error}')

                    username = 'Unknown User'
                    if user_info:
                        username = user_info.get('username', username)

                    if query_id not in self.query_id_user_agent_map:
                        self.query_id_user_agent_map[query_id] = self.get_random_user_agent()

                    log(hju + f'Account: {pth}{idx + 1}/{total}')
                    
                    if use_proxy and self.proxies:
                        proxy = self.proxies[proxy_index]
                        proxy_host = proxy.split('@')[-1]
                        log(hju + f"Proxy: {pth}{proxy_host}")

                        proxy_index = (proxy_index + 1) % len(self.proxies)
                    else:
                        log(pth + "No proxy used or not activate") 

                    log(htm + f"~" * 38)
                    user_info = await self.get_user_info(query_id, proxy, session)            
                    if user_info is not None:
                        user_data = user_info.get('data', {}).get('user')
                        log(hju + f'Username: {pth}{user_data["nickname"]}')
                        log(hju + f'Warbond: {pth}{user_data["warbondTokens"]} {hju}| Honor Point: {pth}{user_data["honorPoints"]} {hju}| Rank: {pth}{user_data["honorPointRank"]}')

                    for _ in range(raid_count):
                        guilds = await self.fetch_guilds(query_id, proxy, session)
                        raid_delay = random.randint(min_raid_delay, max_raid_delay)
                        if guilds:
                            target_guild = guilds[0]
                            log(hju + f"Target guild : {pth}{target_guild['name']} {hju}| Rank: {pth}{target_guild['warbondRank']}")

                            await self.perform_raid(query_id, proxy, session, target_guild['guildId'])
                            await countdown_timer(raid_delay)

                    await countdown_timer(countdown_loop)
                proxy_index = 0  

if __name__ == "__main__":
    _clear()
    _banner()
    bot = MemesWarBot()
    while True:
        try:
            asyncio.run(bot.main())
        except KeyboardInterrupt as e:
            log(mrh + f"Keyboard interrupted by user..")
            exit(0)
