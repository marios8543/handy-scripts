from feedparser import parse
from aiohttp import ClientSession
from discord.ext.commands import Bot
from tinydb import TinyDB, Query
from os.path import join
from os import getenv
from asyncio import sleep
from traceback import print_exc

client = Bot('ab!')
QB_URL = getenv("qbit_url")
INTERVAL = int(getenv("INTERVAL")) if getenv("INTERVAL") else 300
web = ClientSession()
db = TinyDB("animebyter.json")
chn = int(getenv("channel"))

downloading = []

class Anime:
    def __init__(self,name,le,tl,res):
        self.title = name
        self.last_episode = le
        self.torrent_link = tl
        self.resolution = res.strip()

async def login_qb():
    async with web.post(QB_URL+'/login',data={'username':getenv("qbit_user"),'password':getenv("qbit_pass")}) as res:
        if res.status!=200:
            print("Could not authenticate with qBittorrent. Exiting...")
            exit(1)
        else:
            print("Logged in to qBittorrent")

async def get_airing():
    r = []
    res = await web.get("https://animebytes.tv/feed/rss_torrents_airing_anime/{}".format(getenv("ab_key")))
    if res.status==200:
        txt = await res.text()
        rss = parse(txt)
        for i in rss['entries']:
            try:
                title = i['ab_grouptitle']
                ep = int((''.join(x for x in i['ab_torrentproperty'].split("|")[6] if x.isdigit())).strip())
                link = i['link']
                r.append(Anime(title,ep,link,i['ab_torrentproperty'].split("|")[3]))
            except Exception:
                continue
    return r

async def add_torrent(anime):
    print("Adding episode {} of {}".format(anime.last_episode,anime.title))
    path = "/mnt/Storage/Anime"
    try:
        res = await web.post(QB_URL+'/command/download',data={'urls':anime.torrent_link,'savepath':join(path,anime.title),'label':'Anime'})
    except Exception as e:
        print(str(e))
        return
    finally:
        res.close()
    if res.status==200:
        msg = "Added episode {} of {}".format(anime.last_episode,anime.title)
        print(msg)
        return msg
    else:
        print("Failed to add episode {} of {} ({})".format(anime.last_episode,anime.title,res.status))

async def main():
    print("Starting new episode checker")
    while True:
        try:
            print("Checking for new episodes")
            airing = await get_airing()
            for i in airing:
                res = db.search(Query().title==i.title)
                if res:
                    le = res[0]['last_episode']
                    if le<i.last_episode and i.resolution in ("1080p"):
                        msg = await add_torrent(i)
                        if msg:
                            await client.get_channel(chn).send(msg)
                        db.update({'last_episode':i.last_episode},Query().title==i.title)
        except Exception as e:
            print(str(e))
            print_exc()
            continue
        finally:
            await sleep(INTERVAL)

async def dl_watchdog():
    print("Starting download watchdog")
    while True:
        try:
            res = await web.get(QB_URL+"/query/torrents",params={'filter':'downloading','label':'Anime'})
            if res.status==200:
                res = await res.json()
                names = []
                for i in res:
                    names.append(i['name'])
                    if i['name'] not in downloading:
                        downloading.append(i['name'])
                for i in downloading:
                    if i not in names:
                        try:
                                downloading.remove(i)
                        except ValueError:
                            pass
                        await client.get_channel(chn).send(":exclamation: <@!196224042988994560> {} has finished downloading.".format(i))
            else:
                print("Something went wrong with fetching downloads ({}: {})".format(res.status,await res.text()))
        except Exception as e:
            print(str(e))
            print_exc()
            continue
        finally:
            await sleep(10)

def chunks(s, n=1999):
    for start in range(0, len(s), n):
        yield s[start:start+n]

@client.command(pass_context=True)
async def add(ctx):
    airing = await get_airing()
    txt = ""
    for i,v in enumerate(airing):
        txt+="{}) {}\n".format(i,v.title)
    msgs = []
    for i in chunks(txt):
        msgs.append(await ctx.send(i))
    msg = await client.wait_for('message',check=lambda m: m.author==ctx.author and m.channel==ctx.channel)
    await ctx.channel.delete_messages(msgs)
    if msg:
        try:
            msg = int(msg.content)
        except Exception as e:
            return await ctx.send(e)
        if msg>=len(airing):
            return await ctx.send("Invalid number")
        an = airing[msg]
        db.insert({'title':an.title,'last_episode':an.last_episode-1})
        return await ctx.send("Added {}".format(an.title))


@client.command(pass_context=True)
async def remove(ctx):
    watching = db.all()
    txt = ""
    for i,v in enumerate(watching):
        txt+="{}) {}\n".format(i,v['title'])
    msgs = []
    for i in chunks(txt):
        msgs.append(await ctx.send(i))
    msg = await client.wait_for('message',check=lambda m: m.author==ctx.author and m.channel==ctx.channel)
    if len(msgs)==1:
        await msgs[0].delete()
    else:
        await ctx.channel.delete_messages(msgs)
    if msg:
        try:
            msg = int(msg.content)
        except Exception as e:
            return await ctx.send(e)
        if msg>=len(watching):
            return await ctx.send("Invalid number")
        an = watching[msg]
        db.remove(Query().title==an['title'])
        return await ctx.send("Removed {}".format(an))

@client.command(pass_context=True)
async def down(ctx):
    airing = await get_airing()
    txt = ""
    for i,v in enumerate(airing):
        txt+="{}) {} (Episode: {})[{}]\n".format(i,v.title,v.last_episode,v.resolution)
    msgs = []
    for i in chunks(txt):
        msgs.append(await ctx.send(i))
    msg = await client.wait_for('message',check=lambda m: m.author==ctx.author and m.channel==ctx.channel)
    print(msg)
    await ctx.channel.delete_messages(msgs)
    if msg:
        try:
            msg = int(msg.content)
        except Exception as e:
            return await ctx.send(e)
        if msg>=len(airing):
            return await ctx.send("Invalid number")
        await ctx.send(await add_torrent(airing[msg]))

@client.event
async def on_ready():
    print("Starting animebyter")
    await login_qb()
    client.loop.create_task(main())
    client.loop.create_task(dl_watchdog())

client.run(getenv("discord_token"))
